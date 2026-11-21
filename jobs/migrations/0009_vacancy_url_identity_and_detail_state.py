import hashlib
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


def _normalized_url(value):
    try:
        parts = urlsplit(str(value or "").strip())
        scheme = parts.scheme.lower()
        host = (parts.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
        port = parts.port
    except (UnicodeError, ValueError):
        return None
    if scheme not in {"http", "https"} or not host or parts.username or parts.password:
        return None
    netloc = f"[{host}]" if ":" in host else host
    if port and not (scheme == "http" and port == 80 or scheme == "https" and port == 443):
        netloc = f"{netloc}:{port}"
    return urlunsplit((scheme, netloc, parts.path.rstrip("/") or "/", "", ""))


def _hash_url(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def consolidate_exact_url_duplicates(apps, schema_editor):
    db = schema_editor.connection.alias
    Vacancy = apps.get_model("jobs", "Vacancy")
    VacancyAnalysis = apps.get_model("matching", "VacancyAnalysis")
    VacancyOrganization = apps.get_model("matching", "VacancyOrganization")
    AICallAttempt = apps.get_model("matching", "AICallAttempt")
    ProfileVacancyDiscovery = apps.get_model("matching", "ProfileVacancyDiscovery")
    VacancyFollowUp = apps.get_model("dashboard", "VacancyFollowUp")
    ManualVacancySubmission = apps.get_model("jobs", "ManualVacancySubmission")

    groups = {}
    for vacancy in Vacancy.objects.using(db).order_by("pk").iterator(chunk_size=500):
        normalized = _normalized_url(vacancy.original_url)
        marker = _hash_url(normalized) if normalized else None
        Vacancy.objects.using(db).filter(pk=vacancy.pk).update(
            normalized_url=normalized,
            normalized_url_hash=marker,
            dedupe_key=_hash_url(f"{vacancy.source}:{normalized or vacancy.original_url}"),
        )
        if normalized:
            groups.setdefault((vacancy.source, normalized), []).append(vacancy.pk)

    for (source, normalized), ids in groups.items():
        rows = list(Vacancy.objects.using(db).filter(pk__in=ids).order_by("pk"))
        if len(rows) < 2:
            survivor = rows[0]
        else:
            survivor = rows[0]
            duplicate_ids = [row.pk for row in rows[1:]]
            all_ids = [survivor.pk, *duplicate_ids]

            # Keep every analysis record; canonical selection happens at read time.
            VacancyAnalysis.objects.using(db).filter(vacancy_id__in=duplicate_ids).update(vacancy_id=survivor.pk)
            ManualVacancySubmission.objects.using(db).filter(vacancy_id__in=duplicate_ids).update(vacancy_id=survivor.pk)

            discovery_rows = list(
                ProfileVacancyDiscovery.objects.using(db).filter(vacancy_id__in=all_ids)
                .order_by("first_found_at", "pk")
            )
            discovery_by_profile = {}
            for item in discovery_rows:
                discovery_by_profile.setdefault(item.profile_id, []).append(item)
            for profile_rows in discovery_by_profile.values():
                keeper = next((item for item in profile_rows if item.vacancy_id == survivor.pk), profile_rows[0])
                earliest = min(profile_rows, key=lambda item: (item.first_found_at, item.pk))
                evaluated = [item.auto_discard_evaluated_at for item in profile_rows if item.auto_discard_evaluated_at]
                keeper.vacancy_id = survivor.pk
                keeper.first_found_at = earliest.first_found_at
                keeper.auto_discard_threshold = earliest.auto_discard_threshold
                keeper.auto_discard_evaluated_at = max(evaluated) if evaluated else None
                ProfileVacancyDiscovery.objects.using(db).filter(pk=keeper.pk).update(
                    vacancy_id=keeper.vacancy_id,
                    first_found_at=keeper.first_found_at,
                    auto_discard_threshold=keeper.auto_discard_threshold,
                    auto_discard_evaluated_at=keeper.auto_discard_evaluated_at,
                )
                redundant = [item.pk for item in profile_rows if item.pk != keeper.pk]
                ProfileVacancyDiscovery.objects.using(db).filter(pk__in=redundant).delete()

            followup_rows = list(
                VacancyFollowUp.objects.using(db).filter(vacancy_id__in=all_ids).order_by("-updated_at", "-pk")
            )
            followups_by_profile = {}
            for item in followup_rows:
                followups_by_profile.setdefault(item.profile_id, []).append(item)
            for profile_rows in followups_by_profile.values():
                keeper = next((item for item in profile_rows if item.vacancy_id == survivor.pk), profile_rows[0])
                newest = profile_rows[0]
                for field in ("status", "previous_status", "state_changed_at", "archived_at", "updated_at"):
                    setattr(keeper, field, getattr(newest, field))
                keeper.vacancy_id = survivor.pk
                VacancyFollowUp.objects.using(db).filter(pk=keeper.pk).update(
                    vacancy_id=survivor.pk,
                    status=keeper.status,
                    previous_status=keeper.previous_status,
                    state_changed_at=keeper.state_changed_at,
                    archived_at=keeper.archived_at,
                    updated_at=keeper.updated_at,
                )
                redundant = [item.pk for item in profile_rows if item.pk != keeper.pk]
                VacancyFollowUp.objects.using(db).filter(pk__in=redundant).delete()

            organization_rows = list(VacancyOrganization.objects.using(db).filter(vacancy_id__in=all_ids))
            organizations_by_identity = {}
            for item in organization_rows:
                organizations_by_identity.setdefault((item.matching_config_id, item.content_hash), []).append(item)
            for same_content in organizations_by_identity.values():
                same_content.sort(key=lambda item: (item.status == "completed", item.updated_at, item.pk), reverse=True)
                keeper = same_content[0]
                for duplicate in same_content[1:]:
                    VacancyAnalysis.objects.using(db).filter(organization_id=duplicate.pk).update(organization_id=keeper.pk)
                    AICallAttempt.objects.using(db).filter(organization_id=duplicate.pk).update(organization_id=keeper.pk)
                    VacancyOrganization.objects.using(db).filter(pk=duplicate.pk).delete()
            VacancyOrganization.objects.using(db).filter(vacancy_id__in=duplicate_ids).update(vacancy_id=survivor.pk)

            # Merge only fields that are absent; preserve all structured evidence.
            current = Vacancy.objects.using(db).get(pk=survivor.pk)
            newest_first = sorted(rows, key=lambda item: (item.last_seen_at, item.pk))
            raw_data = {}
            for item in newest_first:
                raw_data.update(item.raw_data or {})
            fields = ("company", "location", "description", "salary", "contract_type", "external_id", "published_at")
            merged = {field: getattr(current, field) for field in fields}
            for item in rows[1:]:
                for field in fields:
                    if not merged[field] and getattr(item, field):
                        merged[field] = getattr(item, field)
            confirmed = next((item for item in rows if (item.raw_data or {}).get("details_fetch", {}).get("status") == "confirmed"), None)
            Vacancy.objects.using(db).filter(pk__in=duplicate_ids).delete()
            confirmed_at = None
            if confirmed:
                try:
                    confirmed_at = datetime.fromisoformat(confirmed.raw_data["details_fetch"].get("confirmed_at", ""))
                except (TypeError, ValueError):
                    confirmed_at = None
            Vacancy.objects.using(db).filter(pk=survivor.pk).update(
                original_url=normalized,
                normalized_url=normalized,
                normalized_url_hash=_hash_url(normalized),
                dedupe_key=_hash_url(f"{source}:{normalized}"),
                raw_data=raw_data,
                first_seen_at=min(item.first_seen_at for item in rows),
                last_seen_at=max(item.last_seen_at for item in rows),
                details_status="confirmed" if confirmed else "unknown",
                details_confirmed_at=confirmed_at,
                **merged,
            )
            rows = [survivor]

class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0008_alter_manualvacancysubmission_source_and_more"),
        ("matching", "0015_aicallattempt_format_action_and_repair_stages"),
        ("dashboard", "0004_vacancyfollowup_archived_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="vacancy", name="normalized_url",
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name="vacancy", name="normalized_url_hash",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="vacancy", name="details_status",
            field=models.CharField(choices=[("unknown", "Desconocido"), ("confirmed", "Ficha confirmada")], default="unknown", max_length=12),
        ),
        migrations.AddField(
            model_name="vacancy", name="details_confirmed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RemoveConstraint(model_name="vacancy", name="unique_source_vacancy_identity"),
        migrations.CreateModel(
            name="VacancyURLAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(max_length=80)),
                ("normalized_url", models.CharField(max_length=1000)),
                ("normalized_url_hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("vacancy", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="url_aliases", to="jobs.vacancy")),
            ],
        ),
        migrations.CreateModel(
            name="VacancyDetailLease",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(max_length=80)),
                ("normalized_url", models.CharField(max_length=1000)),
                ("normalized_url_hash", models.CharField(max_length=64)),
                ("token", models.CharField(blank=True, max_length=120)),
                ("expires_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RunPython(consolidate_exact_url_duplicates, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="vacancy",
            constraint=models.UniqueConstraint(fields=("source", "normalized_url_hash"), name="unique_source_normalized_vacancy_url"),
        ),
        migrations.AddConstraint(
            model_name="vacancyurlalias",
            constraint=models.UniqueConstraint(fields=("source", "normalized_url_hash"), name="unique_source_vacancy_url_alias"),
        ),
        migrations.AddConstraint(
            model_name="vacancydetaillease",
            constraint=models.UniqueConstraint(fields=("source", "normalized_url_hash"), name="unique_vacancy_detail_lease"),
        ),
    ]
