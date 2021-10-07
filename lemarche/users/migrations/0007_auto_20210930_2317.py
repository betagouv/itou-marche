# Generated by Django 3.2.7 on 2021-09-30 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_update_user"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={"verbose_name": "Utilisateur", "verbose_name_plural": "Utilisateurs"},
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, unique=True, verbose_name="Adresse e-mail"),
        ),
    ]