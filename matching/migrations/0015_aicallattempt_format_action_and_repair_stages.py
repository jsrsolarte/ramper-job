from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0014_vacancyanalysis_score_stars"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aicallattempt",
            name="stage",
            field=models.CharField(
                choices=[
                    ("scoring", "Puntuación"),
                    ("organization", "Organización"),
                    ("scoring_repair", "Reparación de puntuación"),
                    ("organization_repair", "Reparación de organización"),
                ],
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="aicallattempt",
            name="format_action",
            field=models.CharField(
                choices=[
                    ("direct", "JSON directo"),
                    ("normalized", "Bloque Markdown normalizado"),
                    ("repair_requested", "Reparación solicitada"),
                    ("repair_succeeded", "Reparación completada"),
                ],
                default="direct",
                max_length=24,
            ),
        ),
    ]
