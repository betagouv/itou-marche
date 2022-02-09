import argparse
import json

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand

from lemarche.utils.apis.api_notion import create_block_code, create_text_property, createPage, get_default_client


class Command(BaseCommand):
    """
    Populates BOAMP tenders on notion

    Note: Only on Siae who have coords, filter only on Siae not updated by the API since a two months

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
        # self.stdout_messages_info(["Populating API ZRR...", f"Found {len(siae_list)} Siae"])

        # count_siae_to_update = 0
        client = get_default_client()
        try:
            tenders_to_export = []
            with open("offers_saved.json") as json_file:
                data_tenders = json.load(json_file)
                for tender in data_tenders:
                    # update siae from API
                    tender = self.export_tender_to_notion(client, tender)
                    tenders_to_export.append(tender)
                    # log progress
                    count_tenders_to_export = len(tenders_to_export)
                    if (count_tenders_to_export % 50) == 0:
                        self.stdout_info(f"{count_tenders_to_export}...")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # the real exceed request error have code=10005, with the api
                # but httpx send error code 429 "Unknown Status Code"
                self.stdout_error("exceeded the requests limit for today (5000/per day)")
        finally:
            client.close()
            # we still save siaes zrr status

        self.stdout_messages_sucess(
            [
                f"Done! Processed {len(count_tenders_to_export)}/{len(data_tenders)} tenders",
                f"/tenders_founds success count: {self.success_count['tenders_found']}/{len(count_tenders_to_export)}",
                f"/tenders export success count: {self.success_count['tenders_send_to_notion']}/{len(data_tenders)}",
            ]
        )

    def export_tender_to_notion(self, client, tender):
        # call api is in zrr
        self.success_count["tenders_found"] += 1
        properties = {
            "Name": {"title": [{"text": {"content": tender.get("OBJET", {}).get("TITRE_MARCHE")}}]},
            "Description": {"rich_text": [{"text": {"content": tender.get("OBJET", {}).get("OBJET_COMPLET")}}]},
            "lien": {"url": tender.get("IDENTITE", {}).get("URL_DOCUMENT")},
            "criteres": create_text_property("criteres", tender.get("criteres", "")),
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
