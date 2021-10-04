# Generated by Django 3.2.1 on 2021-06-07 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001bis_create_extensions"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[],
        ),
        migrations.AlterField(
            model_name="user",
            name="api_key",
            field=models.CharField(default=False, max_length=128, verbose_name="Clé API"),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, unique=True, verbose_name="email address"),
        ),
    ]
