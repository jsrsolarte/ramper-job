from django.db import migrations, models
from django.db.models import F


def backfill_completed_at(apps, schema_editor):
    Analysis = apps.get_model("matching", "VacancyAnalysis")
    Analysis.objects.using(schema_editor.connection.alias).filter(
        status="completed", completed_at__isnull=True, updated_at__isnull=False
    ).update(completed_at=F("updated_at"))


class Migration(migrations.Migration):

    dependencies = [
        ("matching", "0008_vacancyanalysis_completed_at"),
    ]

    operations = [
        migrations.RunPython(backfill_completed_at, migrations.RunPython.noop),
    ]
