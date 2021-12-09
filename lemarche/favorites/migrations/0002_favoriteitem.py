# Generated by Django 3.2.8 on 2021-12-02 15:33

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("siaes", "0038_siae_image_count"),
        ("favorites", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FavoriteItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Date de modification")),
                (
                    "favorite_list",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="favorites.favoritelist",
                        verbose_name="Liste de favoris",
                    ),
                ),
                (
                    "siae",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="siaes.siae", verbose_name="Structure"
                    ),
                ),
            ],
            options={
                "verbose_name": "Structure en favoris",
                "verbose_name_plural": "Structures en favoris",
                "ordering": ["-created_at"],
            },
        ),
    ]