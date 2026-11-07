from datetime import datetime, time

from django.db import migrations
from django.utils import timezone
from django.utils.dateparse import parse_date


def backfill_published_at(apps, schema_editor):
    Vacancy = apps.get_model("jobs", "Vacancy")
    alias = schema_editor.connection.alias
    for vacancy in Vacancy.objects.using(alias).filter(published_at__isnull=True).iterator():
        raw_data = vacancy.raw_data or {}
        details = raw_data.get("details") or {}
        posted_date = parse_date(str(details.get("date_posted", "")))
        if posted_date:
            published_at = timezone.make_aware(
                datetime.combine(posted_date, time.min), timezone.get_current_timezone()
            )
            Vacancy.objects.using(alias).filter(pk=vacancy.pk).update(published_at=published_at)


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0003_vacancy_identity_and_publication_date"),
    ]

    operations = [
        migrations.RunPython(backfill_published_at, migrations.RunPython.noop),
    ]
