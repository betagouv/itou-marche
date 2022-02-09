import json
import logging

import httpx


logger = logging.getLogger(__name__)


API_ZRR_REASON = "Récolte des données d'appel d'offre BOAMP"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # "2016-12-31T00:00:00+01:00"  # timezone not managed

# https://boamp-datadila.opendatasoft.com/api/records/1.0/search/?dataset=boamp&q=&rows=10000&sort=dateparution&facet=famille&facet=code_departement&facet=famille_libelle&facet=perimetre&facet=procedure_categorise&facet=nature_categorise_libelle&facet=criteres&facet=marche_public_simplifie&facet=marche_public_simplifie_label&facet=etat&facet=descripteur_code&facet=descripteur_libelle&facet=type_marche&facet=type_marche_facette&facet=type_avis&facet=dateparution&refine.criteres=sociaux&refine.dateparution=2022%2F02
BASE_URL = "https://boamp-datadila.opendatasoft.com/api/records/1.0/search/"


def dump_to_json_file(filename, data):
    with open(f"{filename}.json", "w") as jsonfile:
        json.dump(data, jsonfile)


def get_default_params():
    return {
        "dataset": "boamp",
        "rows": 1000,
        "sort": "dateparution",
        "facet": [
            "famille",
            "famille",
            "code_departement",
            "famille_libelle",
            "perimetre",
            "procedure_categorise",
            "nature_categorise_libelle",
            "criteres",
            "marche_public_simplifie",
            "marche_public_simplifie_label",
            "etat",
            "descripteur_code",
            "descripteur_libelle",
            "type_marche",
            "type_marche_facette",
            "type_avis",
        ],
    }


def get_default_client(params={}):
    params |= get_default_params()
    client = httpx.Client(params=params)
    return client


def get_offers_list(client=None):
    if not client:
        client = get_default_client()

    saved_data = []
    try:
        # refine.criteres=sociaux
        r = client.get(BASE_URL, params={"refine.dateparution": "2022/02"})
        r.raise_for_status()
        data = r.json()
        # add cursor to get all offers if "nbItemsRetournes": 1000 < "nbItemsExistants": 3116
        records = data["records"]
        if records:
            # dump_to_json_file("all_offers", data)
            for offer in records:
                offer_saved = offer.get("fields")
                offer_saved |= json.loads(offer_saved.get("donnees", "[]"))
                offer_saved |= json.loads(offer_saved.get("gestion", "[]"))
                offer_saved["annonces_anterieures"] = json.loads(offer_saved.get("annonces_anterieures", "[]"))
                saved_data.append(offer_saved)

    except httpx.HTTPStatusError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)

    dump_to_json_file("offers_saved", saved_data)
