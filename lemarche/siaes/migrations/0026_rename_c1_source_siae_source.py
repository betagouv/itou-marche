# Generated by Django 3.2.8 on 2021-11-02 09:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("siaes", "0025_alter_siae_kind_with_extra"),
    ]

    operations = [
        migrations.RenameField(
            model_name="siae",
            old_name="c1_source",
            new_name="source",
        ),
    ]