import json
import logging

import httpx


logger = logging.getLogger(__name__)


API_ZRR_REASON = "Mise à jour données ZRR du Marché de la plateforme de l'Inclusion"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # "2016-12-31T00:00:00+01:00"  # timezone not managed

# https://public.opendatasoft.com/explore/dataset/communes-zrr-2017/api/
BASE_URL = "http://www.api.dila.fr/opendata/api-boamp/annonces/"

ENDPOINT_SEARCH = f"{BASE_URL}search"


def get_endpoint_annonce_url(id):
    return f"{BASE_URL}v230/{id}"


def dump_to_json_file(filename, data):
    with open(f"{filename}.json", "w") as jsonfile:
        json.dump(data, jsonfile)


def get_default_params():
    return {}


def get_default_client(params={}):
    params |= get_default_params()
    client = httpx.Client(params=params)
    return client


def get_offer_item(id_offer, client=None):
    if not client:
        client = get_default_client()

    try:
        r = client.get(get_endpoint_annonce_url(id_offer))
        r.raise_for_status()
        data = r.json()
        return data
    except httpx.HTTPStatusError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)


def get_offers_list(client=None):
    if not client:
        client = get_default_client()

    saved_data = []
    try:
        r = client.get(ENDPOINT_SEARCH, params={"criterion": "clause sociale"})
        r.raise_for_status()
        data = r.json()
        # add cursor to get all offers if "nbItemsRetournes": 1000 < "nbItemsExistants": 3116
        records = data["item"]
        if records:
            dump_to_json_file("all_offers", data)
            for offer in records:
                offer_saved = {"id_web": offer["value"], "description": offer["description"]}
                offer_saved["data_api"] = get_offer_item(offer["value"], client)
                saved_data.append(offer_saved)

    except httpx.HTTPStatusError as e:
        logger.error("Error while fetching `%s`: %s", e.request.url, e)

    dump_to_json_file("offers_saved", saved_data)
