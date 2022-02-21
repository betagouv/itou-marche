# Generated by Django 4.0.1 on 2022-02-18 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenders", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="deadline_date",
            field=models.DateField(blank=True, null=True, verbose_name="Date de clôture des réponses"),
        ),
        migrations.AddField(
            model_name="tender",
            name="start_working_date",
            field=models.DateField(blank=True, null=True, verbose_name="Date idéale de début des prestations"),
        ),
    ]
