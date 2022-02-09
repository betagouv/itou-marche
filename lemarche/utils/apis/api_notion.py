import json
import logging

import httpx
from django.conf import settings


logger = logging.getLogger(__name__)


API_NOTION_REASON = "API de communication avec notion (Création de page, database, ...)"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"  # "2016-12-31T00:00:00+01:00"  # timezone not managed

# https://boamp-datadila.opendatasoft.com/api/records/1.0/search/?dataset=boamp&q=&rows=10000&sort=dateparution&facet=famille&facet=code_departement&facet=famille_libelle&facet=perimetre&facet=procedure_categorise&facet=nature_categorise_libelle&facet=criteres&facet=marche_public_simplifie&facet=marche_public_simplifie_label&facet=etat&facet=descripteur_code&facet=descripteur_libelle&facet=type_marche&facet=type_marche_facette&facet=type_avis&facet=dateparution&refine.criteres=sociaux&refine.dateparution=2022%2F02
BASE_URL = "https://api.notion.com/v1/"

headers = {
    "Authorization": f"Bearer {settings.NOTION_TOKEN_API}",
    "Content-Type": "application/json",
    "Notion-Version": settings.NOTION_VERSION_API,
}


def get_endpoint_url(endpoint):
    return f"{BASE_URL}{endpoint}"


def get_default_client(params={}):
    client = httpx.Client(params=params, headers=headers)
    return client


def createPage(databaseId, properties: dict, children: dict, client: httpx.Client = None):
    if not client:
        client = get_default_client()

    createUrl = get_endpoint_url("pages")
    newPageData = {
        "parent": {"type": "database_id", "database_id": databaseId},
        "icon": {"type": "emoji", "emoji": "🎉"},
        "properties": properties,
        "children": children,
    }

    data = json.dumps(newPageData)
    # print(str(uploadData))
    # res = requests.request("POST", createUrl, headers=headers, data=data)

    res = client.post(createUrl, data=data)
    print(res.status_code)
    print(res.text)


def create_block_code(content: dict):
    return {
        "type": "code",
        "code": {
            "text": [
                {
                    "type": "text",
                    "text": {
                        "content": json.dumps(content, indent=4),
                    },
                }
            ],
            "language": "plain text",
        },
    }


def create_text_property(name, content):
    return {"rich_text": [{"text": {"content": content}}]}
