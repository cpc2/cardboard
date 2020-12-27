# Generated by Django 3.1.4 on 2020-12-27 04:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("answers", "0003_auto_20191204_2308"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="answer",
            constraint=models.UniqueConstraint(
                fields=("text", "puzzle"), name="unique_answer_text_per_puzzle"
            ),
        ),
    ]
