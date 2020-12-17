# Generated by Django 3.1.4 on 2020-12-17 01:01

from django.db import migrations, models
import django.db.models.deletion

from hunts.models import Hunt


class Migration(migrations.Migration):

    dependencies = [
        ("hunts", "0004_unique_hunt_slug"),
        ("puzzles", "0016_auto_20201217_0019"),
    ]

    operations = [
        migrations.AddField(
            model_name="puzzletag",
            name="hunt",
            field=models.ForeignKey(
                default=Hunt.objects.order_by("-created_on").first().id,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="puzzle_tags",
                to="hunts.hunt",
            ),
            preserve_default=False,
        ),
    ]
