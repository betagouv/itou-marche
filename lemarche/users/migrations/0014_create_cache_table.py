# Generated by Django 4.0.2 on 2022-03-16 09:10

from django.conf import settings
from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    call_command("createcachetable", settings.CACHES["default"]["LOCATION"])


class Migration(migrations.Migration):
    """
    This migration is used to create the caching table (we use DatabaseCache for Select2).

    The 'users' app has been chosen as entry point because it's central
    dependency on the application and its migrations are processed early in the
    chain.

    More info here:
    - https://docs.djangoproject.com/en/4.0/topics/cache/#database-caching-1
    - https://docs.djangoproject.com/fr/4.0/ref/migration-operations/#django.db.migrations.operations.RunPython
    """

    dependencies = [
        ("users", "0013_user_partner_kind"),
    ]

    operations = [
        migrations.RunPython(create_cache_table, migrations.RunPython.noop),
    ]
