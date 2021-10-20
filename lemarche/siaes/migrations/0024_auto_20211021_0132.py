# Generated by Django 3.2.8 on 2021-10-20 23:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("siaes", "0023_auto_20211021_0129"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siaeuser",
            name="siae",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="siaes.siae", verbose_name="Structure"
            ),
        ),
        migrations.AlterField(
            model_name="siaeuser",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="Utilisateur"
            ),
        ),
    ]
