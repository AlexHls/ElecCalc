# Generated by Django 3.2 on 2021-10-09 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lectureformat", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LectureHall",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "hall_name",
                    models.CharField(
                        max_length=200, verbose_name="Name of the lecture hall"
                    ),
                ),
                (
                    "seating_capacity",
                    models.PositiveIntegerField(
                        verbose_name="Number of available seats"
                    ),
                ),
                (
                    "air_conditioning",
                    models.BooleanField(
                        default=True, verbose_name="Air conditioning available"
                    ),
                ),
                (
                    "beamer_power",
                    models.FloatField(verbose_name="Power consumption of beamer (W)"),
                ),
                (
                    "light_count",
                    models.PositiveIntegerField(
                        verbose_name="Number of available lights"
                    ),
                ),
                (
                    "light_power",
                    models.FloatField(
                        verbose_name="Power consumption of a single light (W)"
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="userinput",
            name="votes",
        ),
        migrations.AlterField(
            model_name="userinput",
            name="choice_text",
            field=models.IntegerField(default=200),
        ),
    ]
