# Generated by Django 4.1.13 on 2024-01-10 09:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("hunts", "0016_hunt_discord_settings"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="hunt",
            options={
                "permissions": (
                    ("hunt_admin", "Hunt admin"),
                    ("hunt_access", "Hunt access"),
                )
            },
        ),
    ]