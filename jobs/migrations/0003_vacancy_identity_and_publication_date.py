import hashlib
import re
import unicodedata

from django.db import migrations, models
from django.utils.text import slugify


def _normalize(value):
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def _identity(vacancy):
    external_id = (vacancy.external_id or "").strip()
    if external_id.isdigit():
        identity = f"external:{external_id}"
    else:
        title = _normalize(vacancy.title)
        location = _normalize(vacancy.location)
        company = _normalize(vacancy.company)
        if title and location:
            identity = f"fingerprint:{title}|{company}|{location}"
        else:
            identity = f"url:{slugify(vacancy.original_url)}"
    return hashlib.sha256(f"{vacancy.source}:{identity}".encode("utf-8")).hexdigest()


def consolidate_vacancies(apps, schema_editor):
    Vacancy = apps.get_model("jobs", "Vacancy")
    VacancyAnalysis = apps.get_model("matching", "VacancyAnalysis")
    db = schema_editor.connection.alias

    groups = {}
    for vacancy in Vacancy.objects.using(db).order_by("pk").iterator():
        key = _identity(vacancy)
        vacancy.dedupe_key = key
        groups.setdefault((vacancy.source, key), []).append(vacancy)

    for (source, key), duplicates in groups.items():
        survivor = duplicates[0]
        raw_data = dict(survivor.raw_data or {})
        alternate_urls = list(raw_data.get("alternate_urls", []))
        duplicate_ids = [vacancy.pk for vacancy in duplicates]
        for duplicate in duplicates[1:]:
            if duplicate.original_url != survivor.original_url and duplicate.original_url not in alternate_urls:
                alternate_urls.append(duplicate.original_url)
            for url in (duplicate.raw_data or {}).get("alternate_urls", []):
                if url != survivor.original_url and url not in alternate_urls:
                    alternate_urls.append(url)
            for field in ("company", "location", "description", "salary", "contract_type", "external_id"):
                if not getattr(survivor, field) and getattr(duplicate, field):
                    setattr(survivor, field, getattr(duplicate, field))
            raw_data.update(duplicate.raw_data or {})

        raw_data.pop("alternate_urls", None)
        if alternate_urls:
            raw_data["alternate_urls"] = alternate_urls
        updates = {"dedupe_key": key, "raw_data": raw_data}
        for field in ("company", "location", "description", "salary", "contract_type", "external_id"):
            updates[field] = getattr(survivor, field)
        Vacancy.objects.using(db).filter(pk=survivor.pk).update(**updates)

        analysis_groups = {}
        for analysis in VacancyAnalysis.objects.using(db).filter(vacancy_id__in=duplicate_ids).iterator():
            combination = (analysis.profile_id, analysis.profile_revision_id, analysis.matching_config_id)
            analysis_groups.setdefault(combination, []).append(analysis)
        for analyses in analysis_groups.values():
            analyses.sort(key=lambda item: (item.status == "completed", item.updated_at, item.pk), reverse=True)
            keep = analyses[0]
            VacancyAnalysis.objects.using(db).filter(pk=keep.pk).update(vacancy_id=survivor.pk)
            redundant_ids = [analysis.pk for analysis in analyses[1:]]
            if redundant_ids:
                VacancyAnalysis.objects.using(db).filter(pk__in=redundant_ids).delete()

        Vacancy.objects.using(db).filter(pk__in=[vacancy.pk for vacancy in duplicates[1:]]).delete()


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("jobs", "0002_jobsourcestatus"),
        ("matching", "0003_profile_search_and_structured_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="vacancy",
            name="dedupe_key",
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="vacancy",
            name="published_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(consolidate_vacancies, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="vacancy",
            name="dedupe_key",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddConstraint(
            model_name="vacancy",
            constraint=models.UniqueConstraint(fields=("source", "dedupe_key"), name="unique_source_vacancy_identity"),
        ),
    ]
