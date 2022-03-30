import logging
import os

from django.core.management.base import BaseCommand

from lemarche.perimeters.models import Perimeter


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class Command(BaseCommand):
    """
    Import French country

    To debug:
        django-admin import_country --dry-run
        django-admin import_country --dry-run --verbosity=2

    To populate the database:
        django-admin import_country
    """

    help = "Import the French country."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Only print data to import")

    def set_logger(self, verbosity):
        """
        Set logger level based on the verbosity option.
        """
        handler = logging.StreamHandler(self.stdout)

        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False
        self.logger.addHandler(handler)

        self.logger.setLevel(logging.INFO)
        if verbosity > 1:
            self.logger.setLevel(logging.DEBUG)

    def handle(self, dry_run=False, **options):
        self.stdout.write("-" * 80)
        self.stdout.write("Importing Perimeters > country...")
        self.stdout.write(
            f"Before: {Perimeter.objects.filter(kind=Perimeter.KIND_COUNTRY).count()} {Perimeter.KIND_COUNTRY}"
        )

        self.set_logger(options.get("verbosity"))

        name = "France entière"
        slug = "france"

        self.logger.debug("-" * 80)
        self.logger.debug(name)

        if not dry_run:
            Perimeter.objects.get_or_create(
                kind=Perimeter.KIND_COUNTRY,
                name=name,
                slug=slug,
            )

        self.stdout.write("Done.")
        self.stdout.write(
            f"After: {Perimeter.objects.filter(kind=Perimeter.KIND_COUNTRY).count()} {Perimeter.KIND_COUNTRY}"
        )
