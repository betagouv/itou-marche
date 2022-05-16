# Generated by Django 4.0.4 on 2022-05-11 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenders", "0011_merge_20220512_1802"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="siae_interested_list_last_seen_date",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Date de dernière visite de l'auteur sur la page 'structures intéressées'",
            ),
        ),
    ]
