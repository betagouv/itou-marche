from django.core.management.base import BaseCommand

from lemarche.utils.apis.api_boamp import get_offers_list


class Command(BaseCommand):
    """ """

    def handle(self, *args, **options):
        get_offers_list()
