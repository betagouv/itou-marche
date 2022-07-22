import argparse
import json
from datetime import datetime

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from lemarche.utils.apis.api_notion import (
    create_block_code,
    create_date_property,
    create_text_property,
    createPage,
    get_default_client,
)


class Command(BaseCommand):
    """
    Populates BOAMP tenders on notion

    Usage: poetry run python manage.py export_tenders_to_notion
    Usage: poetry run python manage.py export_tenders_to_notion --limit 10
    Usage: poetry run python manage.py export_tenders_to_notion --force
    Usage: poetry run python manage.py export_tenders_to_notion --limit 100 --no-force
    """

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.success_count = {"tenders_found": 0, "tenders_send_to_notion": 0}

    def add_arguments(self, parser):
        parser.add_argument(
            "-L", "--limit", type=int, default=None, help="Limiter le nombre de structures à processer"
        )
        parser.add_argument(
            "-F",
            "--force",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Forcer l'update sans la vérification de la dernière mise à jour",
        )

    def handle(self, *args, **options):
        # self.stdout_messages_info(["Populating API BOAMP...", f"Found {len(0)} Tenders"])

        client = get_default_client()
        tenders_to_export = []
        count_tenders_to_export = 0
        with open("offers_saved.json") as json_file:
            data_tenders = json.load(json_file)
            try:
                for tender in data_tenders:
                    try:
                        tender = self.export_tender_to_notion(client, tender)
                        tenders_to_export.append(tender)
                        count_tenders_to_export = len(tenders_to_export)
                    except requests.exceptions.HTTPError as e:
                        status_code = e.response.status_code
                        if status_code == 429:
                            # the real exceed request error have code=10005, with the api
                            # but httpx send error code 429 "Unknown Status Code"
                            self.stdout_error("exceeded the requests limit for today (5000/per day)")
                    except requests.exceptions.ReadTimeout:
                        self.stdout_error("Readtimeout for this tender : ")
                        self.stdout_error(tender)
                    if (count_tenders_to_export % 50) == 0:
                        self.stdout_info(f"{count_tenders_to_export}...")
            finally:
                client.close()
                self.stdout_messages_sucess(
                    [
                        f"Done! Processed {len(count_tenders_to_export)}/{len(data_tenders)} tenders",
                    ]
                )

    def get_cpv_fields(self, tender):
        cpvs = tender.get("OBJET", {}).get("CPV", {})
        if type(cpvs) == list:
            return ",".join([cpv.get("PRINCIPAL") for cpv in cpvs])
        else:
            return cpvs.get("PRINCIPAL")

    def get_date_conversion(self, tender_date):
        return datetime.strptime(tender_date, "%Y-%m-%d")

    def export_tender_to_notion(self, client, tender):
        self.success_count["tenders_found"] += 1
        properties = {
            "Name": {"title": [{"text": {"content": tender.get("OBJET", {}).get("TITRE_MARCHE", "")}}]},
            "Description": {"rich_text": [{"text": {"content": tender.get("OBJET", {}).get("OBJET_COMPLET")}}]},
            "criteres": create_text_property(tender.get("criteres")),
            "cpv": create_text_property(self.get_cpv_fields(tender)),
            "descripteur_libelle": create_text_property(tender.get("descripteur_libelle")),
            "marche_public_simplifie": create_text_property(tender.get("marche_public_simplifie")),
            "nomacheteur": create_text_property(tender.get("nomacheteur")),
            "Type de marché": create_text_property(tender.get("type_marche_facette")),
            "Famille libelle": create_text_property(tender.get("famille_libelle")),
            "Code departement": create_text_property(tender.get("code_departement")),
            "Date de parution": create_date_property(
                self.get_date_conversion(tender.get("dateparution")),
                self.get_date_conversion(tender.get("datefindiffusion")),
            ),
            "Réservé": create_text_property(
                "true"
                if tender.get("OBJET", {}).get("MARCHE_RESERVE_OUI", False)
                or tender.get("CONDITION_PARTICIPATION", {}).get("MARCHE_RESERVE_OUI", False)
                else "false"
            ),
            "Date de fin de diffusion": create_date_property(self.get_date_conversion(tender.get("datefindiffusion"))),
        }
        identity_tenders = tender.get("IDENTITE")
        if identity_tenders:
            properties |= {
                "lien": {"url": identity_tenders.get("URL_DOCUMENT") or identity_tenders.get("URL_PROFIL_ACHETEUR")},
                "Nom du prospect": create_text_property(identity_tenders.get("DENOMINATION")),
                "Nom du contact du prospect": create_text_property(identity_tenders.get("CONTACT")),
                "Code postal du prospect": create_text_property(identity_tenders.get("CP")),
                "Ville du prospect": create_text_property(identity_tenders.get("VILLE")),
                "Tel du prospect": create_text_property(identity_tenders.get("TEL")),
                "Email du prospect": create_text_property(identity_tenders.get("MEL")),
            }

        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"text": [{"type": "text", "text": {"content": "Source"}}]},
            },
            create_block_code(tender.get("IDENTITE")),
            create_block_code(tender.get("OBJET")),
            create_block_code(tender.get("PROCEDURE")),
            create_block_code(tender.get("CONDITION_PARTICIPATION")),
        ]
        createPage(settings.NOTION_DATABASES_BOAMP_API, properties=properties, children=children, client=client)
        self.success_count["tenders_send_to_notion"] += 1

    def stdout_success(self, message):
        return self.stdout.write(self.style.SUCCESS(message))

    def stdout_error(self, message):
        return self.stdout.write(self.style.ERROR(message))

    def stdout_info(self, message):
        return self.stdout.write(self.style.HTTP_INFO(message))

    def stdout_messages_info(self, messages):
        self.stdout_info("-" * 80)
        for message in messages:
            self.stdout_info(message)
        self.stdout_info("-" * 80)

    def stdout_messages_sucess(self, messages):
        self.stdout_success("-" * 80)
        for message in messages:
            self.stdout_success(message)
        self.stdout_success("-" * 80)
