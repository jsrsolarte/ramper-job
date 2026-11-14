import logging
import time
import uuid
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from matching.models import MatchingConfig, ProfileVacancyDiscovery
from matching.services import get_active_matching_config, get_profile_search_terms
from operations.models import (
    AdminCommandRun,
    OperationalRun,
    RefreshBatch,
    RefreshBatchProfile,
    RefreshWorkItem,
    RefreshWorkProfile,
)
from operations.services import (
    begin_run,
    claim_refresh_lease,
    finish_run,
    record_admin_profile_result,
    release_refresh_lease,
    renew_refresh_lease,
)
from profiles.locations import expand_locations, vacancy_location_is_eligible
from profiles.models import Profile
from .models import JobSourceStatus

from .connectors.base import JobListing, SourcePartiallyUnavailable, SourceUnavailable
from .search_groups import group_search_requests, search_request_identity
from .services import save_listings

logger = logging.getLogger(__name__)

WORK_LEASE_SECONDS = settings.REFRESH_WORK_LEASE_SECONDS
DETAIL_BATCH_SIZE = settings.REFRESH_DETAIL_BATCH_SIZE
LOCATION_BATCH_SIZE = settings.REFRESH_LOCATION_BATCH_SIZE


def _configured_connectors():
    # Keep the historical jobs.tasks injection point usable by existing integrations.
    from jobs.tasks import configured_connectors

    return configured_connectors()


def _listing_to_json(listing):
    return {
        "source": listing.source,
        "external_id": listing.external_id or "",
        "title": listing.title,
        "company": listing.company,
        "location": listing.location,
        "description": listing.description,
        "original_url": listing.original_url,
        "raw_data": listing.raw_data or {},
        "salary": listing.salary,
        "contract_type": listing.contract_type,
    }


def _listing_from_json(value):
    return JobListing(**value)


def _enqueue_work_item(work_item_id):
    now = timezone.now()
    updated = RefreshWorkItem.objects.filter(
        pk=work_item_id,
        status=RefreshWorkItem.Status.QUEUED,
    ).update(last_dispatched_at=now)
    if updated:
        process_refresh_work_item.delay(work_item_id)


def _finish_batch_profile(batch_profile_id, *, failed=False, stale=False):
    with transaction.atomic():
        profile_run = None
        batch_profile = RefreshBatchProfile.objects.select_for_update().select_related(
            "batch", "profile_run", "profile",
        ).filter(pk=batch_profile_id).first()
        if batch_profile is None or batch_profile.finished_at:
            return False
        if not batch_profile.prepared_at or not batch_profile.batch.planned_at:
            return False

        unfinished = batch_profile.work_links.exclude(
            work_item__status__in=(
                RefreshWorkItem.Status.SUCCEEDED,
                RefreshWorkItem.Status.PARTIAL,
                RefreshWorkItem.Status.FAILED,
            ),
        ).exists()
        if unfinished:
            return False

        links = list(batch_profile.work_links.select_related("work_item__source_run"))
        work_failed = failed or batch_profile.failed
        for link in links:
            item = link.work_item
            source_results = dict(batch_profile.source_results or {})
            result = source_results.setdefault(item.source, {"queries": 0, "failures": 0, "vacancy_ids": []})
            result["queries"] += 1
            if item.status in (RefreshWorkItem.Status.PARTIAL, RefreshWorkItem.Status.FAILED):
                result["failures"] = result.get("failures", 0) + 1
                work_failed = True
            batch_profile.source_results = source_results

        source_results = dict(batch_profile.source_results or {})
        found_ids = set(batch_profile.found_vacancy_ids or [])
        for source, summary in source_results.items():
            summary["count"] = len(set(summary.pop("vacancy_ids", [])))
            summary["source"] = source
            summary["available"] = not summary.get("failures", 0)

        batch_profile.failed = work_failed
        batch_profile.stale = batch_profile.stale or stale
        batch_profile.source_results = source_results
        batch_profile.finished_at = timezone.now()
        batch_profile.save(update_fields=("failed", "stale", "source_results", "finished_at"))

        profile_run = batch_profile.profile_run
        run_status = OperationalRun.Status.FAILED if work_failed and not found_ids else (
            OperationalRun.Status.PARTIAL if work_failed or batch_profile.stale else OperationalRun.Status.SUCCEEDED
        )
        finish_run(
            profile_run,
            status=run_status,
            item_count=len(found_ids),
            error_category="source_error" if work_failed or batch_profile.stale else "",
        )

        batch = batch_profile.batch
        if not batch.profiles.filter(finished_at__isnull=True).exists():
            profile_states = list(batch.profiles.values_list("failed", "stale"))
            if profile_states and all(is_failed for is_failed, _ in profile_states):
                batch.status = RefreshBatch.Status.FAILED
            elif any(is_failed or is_stale for is_failed, is_stale in profile_states):
                batch.status = RefreshBatch.Status.PARTIAL
            else:
                batch.status = RefreshBatch.Status.SUCCEEDED
            batch.finished_at = timezone.now()
            batch.heartbeat_at = batch.finished_at
            batch.save(update_fields=("status", "finished_at", "heartbeat_at"))

    release_refresh_lease(f"profile-refresh:{batch_profile.profile_id}", batch_profile.lease_token)
    if batch_profile.batch.command_id:
        record_admin_profile_result(
            batch_profile.batch.command_id,
            results=list(batch_profile.source_results.values()),
            failed=batch_profile.failed or batch_profile.stale,
        )
    return True


def _record_work_failure(item, *, status, error_category):
    now = timezone.now()
    item = RefreshWorkItem.objects.select_related("source_run").get(pk=item.pk)
    item.status = status
    item.phase = RefreshWorkItem.Phase.COMPLETE
    item.error_category = error_category[:80]
    item.finished_at = now
    item.heartbeat_at = now
    item.lease_token = ""
    item.lease_expires_at = None
    item.save(update_fields=(
        "status", "phase", "error_category", "finished_at", "heartbeat_at", "lease_token", "lease_expires_at",
    ))
    finish_run(
        item.source_run,
        status=OperationalRun.Status.PARTIAL if status == RefreshWorkItem.Status.PARTIAL else OperationalRun.Status.FAILED,
        item_count=item.source_run.item_count,
        new_count=item.source_run.new_count,
        known_count=item.source_run.known_count,
        known_updated_count=item.source_run.known_updated_count,
        known_unchanged_count=item.source_run.known_unchanged_count,
        listing_count=item.listing_count,
        title_kept_count=item.title_kept_count,
        title_discarded_count=item.title_discarded_count,
        details_requested_count=item.details_requested_count,
        details_received_count=item.details_received_count,
        title_input_tokens=item.title_input_tokens,
        error_category=error_category,
    )
    JobSourceStatus.objects.update_or_create(
        source=item.source,
        defaults={
            "available": False,
            "status_message": "La fuente de empleo no respondió." if error_category == "source_unavailable" else "No fue posible completar la consulta a la fuente.",
            "last_checked_at": now,
        },
    )
    profile_ids = list(item.profile_links.values_list("batch_profile_id", flat=True))
    for profile_id in profile_ids:
        _finish_batch_profile(profile_id, failed=True)


def _retry_work_item(item_id, token, error_category):
    with transaction.atomic():
        item = RefreshWorkItem.objects.select_for_update().filter(
            pk=item_id,
            status=RefreshWorkItem.Status.RUNNING,
            lease_token=token,
        ).first()
        if item is None:
            return False
        item.attempts += 1
        if item.attempts >= 4:
            item.error_category = error_category[:80]
            item.save(update_fields=("attempts", "error_category"))
            terminal = True
        else:
            item.status = RefreshWorkItem.Status.QUEUED
            item.error_category = error_category[:80]
            item.lease_token = ""
            item.lease_expires_at = None
            item.heartbeat_at = timezone.now()
            item.last_dispatched_at = item.heartbeat_at
            item.save(update_fields=(
                "attempts", "status", "error_category", "lease_token", "lease_expires_at",
                "heartbeat_at", "last_dispatched_at",
            ))
            terminal = False
    if terminal:
        _record_work_failure(item, status=RefreshWorkItem.Status.FAILED, error_category=error_category)
    else:
        process_refresh_work_item.apply_async(args=(item_id,), countdown=30 * item.attempts)
    return True


@shared_task(name="jobs.resumable.prepare_refresh_batch")
def prepare_refresh_batch(profile_leases, command_run_id=None, leases_already_claimed=False):
    from jobs.tasks import refresh_sources
    from operations.parameters import processing_is_paused

    if not profile_leases:
        if command_run_id:
            command = AdminCommandRun.objects.filter(pk=command_run_id).first()
            if command and command.status == AdminCommandRun.Status.RUNNING and command.completed_profiles < command.profile_count:
                for _ in range(command.profile_count - command.completed_profiles):
                    record_admin_profile_result(command_run_id, results=[])
        return {"scheduled_profiles": 0}
    if processing_is_paused():
        for profile_id, token in profile_leases.items():
            release_refresh_lease(f"profile-refresh:{int(profile_id)}", token)
        refresh_sources.apply_async(kwargs={"command_run_id": command_run_id}, countdown=60)
        return {"deferred": "processing_paused"}

    claimed = {}
    for profile_id_value, token in profile_leases.items():
        profile_id = int(profile_id_value)
        profile_enabled = Profile.objects.filter(
            pk=profile_id,
            owner__is_active=True,
            search_enabled=True,
            cv_file__gt="",
            revision_number__gt=0,
        ).exists()
        if not profile_enabled:
            release_refresh_lease(f"profile-refresh:{profile_id}", token)
            if command_run_id:
                record_admin_profile_result(command_run_id, results=[])
            continue
        lease_key = f"profile-refresh:{profile_id}"
        lease_ok = (
            renew_refresh_lease(lease_key, token, ttl_seconds=24 * 60 * 60)
            if leases_already_claimed
            else claim_refresh_lease(lease_key, token)
        )
        if lease_ok:
            renew_refresh_lease(f"profile-refresh:{profile_id}", token, ttl_seconds=24 * 60 * 60)
            claimed[profile_id] = token
        elif command_run_id:
            record_admin_profile_result(command_run_id, results=[])
    if not claimed:
        return {"scheduled_profiles": 0}

    batch = RefreshBatch.objects.create(
        command_id=command_run_id,
        status=RefreshBatch.Status.RUNNING,
        started_at=timezone.now(),
    )
    scheduled = 0
    for profile_id, token in claimed.items():
        profile = Profile.objects.select_related("owner").filter(
            pk=profile_id, owner__is_active=True, cv_file__gt="", revision_number__gt=0,
        ).first()
        if profile is None:
            release_refresh_lease(f"profile-refresh:{profile_id}", token)
            if command_run_id:
                record_admin_profile_result(command_run_id, results=[], failed=True)
            continue
        revision = profile.revisions.filter(version=profile.revision_number).first()
        if revision is None:
            release_refresh_lease(f"profile-refresh:{profile_id}", token)
            if command_run_id:
                record_admin_profile_result(command_run_id, results=[], failed=True)
            continue
        profile_run = begin_run(kind=OperationalRun.Kind.INGESTION, operation="profile_refresh")
        batch_profile = RefreshBatchProfile.objects.create(
            batch=batch,
            profile=profile,
            profile_run=profile_run,
            lease_token=token,
        )
        prepare_refresh_profile.delay(batch_profile.pk)
        scheduled += 1

    if not scheduled:
        plan_refresh_batch.delay(batch.pk)
    return {"scheduled_profiles": scheduled}


@shared_task(bind=True, name="jobs.resumable.prepare_refresh_profile", max_retries=3)
def prepare_refresh_profile(self, batch_profile_id):
    from matching.client import OmniRouteError
    from operations.parameters import processing_is_paused

    batch_profile = RefreshBatchProfile.objects.select_related("batch", "profile").filter(
        pk=batch_profile_id,
    ).first()
    if batch_profile is None or batch_profile.prepared_at:
        return {"skipped": "already_prepared"}
    if not Profile.objects.filter(
        pk=batch_profile.profile_id,
        owner__is_active=True,
        search_enabled=True,
    ).exists():
        batch_profile.search_request = {}
        batch_profile.prepared_at = timezone.now()
        batch_profile.save(update_fields=("search_request", "prepared_at"))
        plan_refresh_batch.delay(batch_profile.batch_id)
        return {"skipped": "profile_search_paused_or_inactive"}
    if processing_is_paused():
        RefreshBatch.objects.filter(pk=batch_profile.batch_id).update(heartbeat_at=timezone.now())
        renew_refresh_lease(
            f"profile-refresh:{batch_profile.profile_id}",
            batch_profile.lease_token,
            ttl_seconds=24 * 60 * 60,
        )
        prepare_refresh_profile.apply_async(args=(batch_profile_id,), countdown=60)
        return {"deferred": "processing_paused"}

    profile = Profile.objects.select_related("owner").filter(
        pk=batch_profile.profile_id,
        owner__is_active=True,
        search_enabled=True,
        cv_file__gt="",
        revision_number__gt=0,
    ).first()
    revision = profile.revisions.filter(version=profile.revision_number).first() if profile else None
    if revision is None:
        batch_profile.failed = True
        batch_profile.prepared_at = timezone.now()
        batch_profile.save(update_fields=("failed", "prepared_at"))
        plan_refresh_batch.delay(batch_profile.batch_id)
        return {"failed": "profile_revision_missing"}

    config = get_active_matching_config()
    try:
        terms = get_profile_search_terms(revision, config)
    except OmniRouteError as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        logger.warning("profile_search_terms_failed category=%s", exc.category)
        batch_profile.failed = True
        batch_profile.prepared_at = timezone.now()
        batch_profile.save(update_fields=("failed", "prepared_at"))
        plan_refresh_batch.delay(batch_profile.batch_id)
        return {"failed": exc.category}
    except Exception as exc:
        logger.error("profile_search_terms_failed exception_type=%s", type(exc).__name__)
        batch_profile.failed = True
        batch_profile.prepared_at = timezone.now()
        batch_profile.save(update_fields=("failed", "prepared_at"))
        plan_refresh_batch.delay(batch_profile.batch_id)
        return {"failed": "search_terms_error"}

    batch_profile.search_request = {
        "profile_id": profile.pk,
        "revision_id": revision.pk,
        "matching_config_id": config.pk,
        "keywords": list(terms.keywords),
        "locations": expand_locations(revision.locations),
        "remote_ok": revision.remote_ok,
    }
    batch_profile.prepared_at = timezone.now()
    batch_profile.save(update_fields=("search_request", "prepared_at"))
    plan_refresh_batch.delay(batch_profile.batch_id)
    return {"prepared": True}


@shared_task(name="jobs.resumable.plan_refresh_batch")
def plan_refresh_batch(batch_id):
    item_ids = []
    with transaction.atomic():
        batch = RefreshBatch.objects.select_for_update().filter(pk=batch_id).first()
        if batch is None or batch.planned_at:
            return {"skipped": "already_planned"}
        profiles = list(batch.profiles.select_related("profile").order_by("pk"))
        if any(not batch_profile.prepared_at for batch_profile in profiles):
            return {"waiting": True}
        requests = []
        batch_profiles = {bp.profile_id: bp for bp in profiles}
        for batch_profile in profiles:
            if not batch_profile.profile.search_enabled:
                continue
            request = batch_profile.search_request
            locations = request.get("locations", [])
            location_chunks = [
                locations[index:index + LOCATION_BATCH_SIZE]
                for index in range(0, len(locations), LOCATION_BATCH_SIZE)
            ] or [[]]
            for keyword in request.get("keywords", []):
                for chunk_index, location_chunk in enumerate(location_chunks):
                    requests.append({
                        "profile_id": batch_profile.profile_id,
                        "revision_id": request.get("revision_id"),
                        "matching_config_id": request.get("matching_config_id"),
                        "keywords": [keyword],
                        "locations": location_chunk,
                        "remote_ok": request.get("remote_ok", False) and chunk_index == 0,
                    })

        for connector in _configured_connectors():
            for group in group_search_requests(connector, requests):
                request = group["request"]
                identity = search_request_identity(connector, request)
                source_run = begin_run(
                    kind=OperationalRun.Kind.INGESTION,
                    operation="source_query",
                    source=connector.source,
                )
                item = RefreshWorkItem.objects.create(
                    batch=batch,
                    source_run=source_run,
                    source=connector.source,
                    identity=identity,
                    search_request={
                        "keywords": request["keywords"],
                        "locations": request["locations"],
                        "remote_ok": request["remote_ok"],
                        "matching_config_id": request["matching_config_id"],
                    },
                )
                links = [
                    RefreshWorkProfile(
                        work_item=item,
                        batch_profile=batch_profiles[member["profile_id"]],
                        revision_id=member["revision_id"],
                    )
                    for member in group["members"]
                    if member["profile_id"] in batch_profiles
                ]
                RefreshWorkProfile.objects.bulk_create(links, ignore_conflicts=True)
                item_ids.append(item.pk)
        batch.planned_at = timezone.now()
        batch.heartbeat_at = batch.planned_at
        batch.save(update_fields=("planned_at", "heartbeat_at"))

    for batch_profile in profiles:
        _finish_batch_profile(batch_profile.pk, failed=batch_profile.failed)
    for item_id in item_ids:
        _enqueue_work_item(item_id)
    if not profiles:
        RefreshBatch.objects.filter(pk=batch_id).update(
            status=RefreshBatch.Status.FAILED,
            finished_at=timezone.now(),
        )
    return {"scheduled_units": len(item_ids), "profiles": len(profiles)}

def _claim_work_item(work_item_id):
    now = timezone.now()
    token = uuid.uuid4().hex
    with transaction.atomic():
        item = RefreshWorkItem.objects.select_for_update().filter(pk=work_item_id).first()
        if item is None or item.status in (
            RefreshWorkItem.Status.SUCCEEDED,
            RefreshWorkItem.Status.PARTIAL,
            RefreshWorkItem.Status.FAILED,
        ):
            return None
        if item.status == RefreshWorkItem.Status.RUNNING and item.lease_expires_at and item.lease_expires_at > now:
            return None
        item.status = RefreshWorkItem.Status.RUNNING
        item.lease_token = token
        item.lease_expires_at = now + timedelta(seconds=WORK_LEASE_SECONDS)
        item.heartbeat_at = now
        item.save(update_fields=("status", "attempts", "lease_token", "lease_expires_at", "heartbeat_at"))
        for link in item.profile_links.select_related("batch_profile"):
            batch_profile = link.batch_profile
            renew_refresh_lease(
                f"profile-refresh:{batch_profile.profile_id}",
                batch_profile.lease_token,
                ttl_seconds=24 * 60 * 60,
            )
        return item, token


def _increment_run_metrics(item, saved, detail_ms=0):
    run = OperationalRun.objects.select_for_update().get(pk=item.source_run_id)
    run.item_count += len(saved.vacancies)
    run.new_count = (run.new_count or 0) + saved.new_count
    run.known_count = (run.known_count or 0) + saved.known_count
    run.known_updated_count = (run.known_updated_count or 0) + saved.known_updated_count
    run.known_unchanged_count = (run.known_unchanged_count or 0) + saved.known_unchanged_count
    run.details_received_count = (run.details_received_count or 0) + len(saved.vacancies)
    run.detail_fetch_duration_ms = (run.detail_fetch_duration_ms or 0) + max(0, int(detail_ms))
    run.save(update_fields=(
        "item_count", "new_count", "known_count", "known_updated_count", "known_unchanged_count",
        "details_received_count", "detail_fetch_duration_ms",
    ))


def _persist_listing_chunk(item_id, token, start, listings, *, detail_ms=0, available=True):
    from matching.tasks import schedule_vacancy_analysis

    with transaction.atomic():
        item = RefreshWorkItem.objects.select_for_update().filter(
            pk=item_id, status=RefreshWorkItem.Status.RUNNING, lease_token=token,
        ).first()
        if item is None or item.cursor != start:
            return False
        saved = save_listings(listings)
        links = list(item.profile_links.select_related("batch_profile__profile"))
        current_config_id = MatchingConfig.objects.filter(is_active=True).order_by("-version").values_list("pk", flat=True).first()
        targets = {}
        valid_links = []
        for link in links:
            batch_profile = link.batch_profile
            profile = Profile.objects.select_related("owner").filter(
                pk=batch_profile.profile_id,
                owner__is_active=True,
                search_enabled=True,
                cv_file__gt="",
            ).first()
            revision = profile.revisions.filter(
                pk=link.revision_id,
                version=profile.revision_number,
            ).first() if profile else None
            if revision is None or current_config_id != item.search_request.get("matching_config_id"):
                batch_profile.stale = True
                batch_profile.save(update_fields=("stale",))
                continue
            valid_links.append((link, batch_profile, profile, revision))

        for link, batch_profile, profile, revision in valid_links:
            for vacancy in saved.vacancies:
                if not vacancy_location_is_eligible(vacancy, revision):
                    continue
                ProfileVacancyDiscovery.objects.get_or_create(
                    profile_id=profile.pk,
                    vacancy_id=vacancy.pk,
                    defaults={"auto_discard_threshold": profile.min_score or 0},
                )
                target = targets.setdefault(vacancy.pk, {
                    "vacancy": vacancy,
                    "profile_revisions": {},
                    "run_ids": {},
                    "materially_changed": False,
                })
                target["profile_revisions"][str(profile.pk)] = link.revision_id
                target["run_ids"].setdefault(str(profile.pk), []).append(item.source_run_id)
                target["materially_changed"] = target["materially_changed"] or getattr(vacancy, "_materially_changed", False)
                ids = set(batch_profile.found_vacancy_ids or [])
                ids.add(vacancy.pk)
                batch_profile.found_vacancy_ids = sorted(ids)
                source_results = dict(batch_profile.source_results or {})
                result = source_results.setdefault(item.source, {"queries": 0, "failures": 0, "vacancy_ids": []})
                result["vacancy_ids"] = sorted(set(result["vacancy_ids"]) | {vacancy.pk})
                batch_profile.source_results = source_results
                batch_profile.save(update_fields=("found_vacancy_ids", "source_results"))

        for target in targets.values():
            transaction.on_commit(lambda target=target: schedule_vacancy_analysis.delay(
                target["vacancy"].pk,
                force_reanalysis=target["materially_changed"],
                profile_ids=[int(profile_id) for profile_id in target["profile_revisions"]],
                expected_revision_ids=target["profile_revisions"],
                expected_matching_config_id=item.search_request.get("matching_config_id"),
                source_query_run_ids_by_profile=target["run_ids"],
            ))

        item.cursor = start + len(listings)
        item.available = item.available and available
        item.details_received_count += len(saved.vacancies)
        item.heartbeat_at = timezone.now()
        item.lease_expires_at = item.heartbeat_at + timedelta(seconds=WORK_LEASE_SECONDS)
        item.batch.heartbeat_at = item.heartbeat_at
        item.batch.save(update_fields=("heartbeat_at",))
        _increment_run_metrics(item, saved, detail_ms=detail_ms)
        item.attempts = 0
        item.save(update_fields=("cursor", "available", "details_received_count", "heartbeat_at", "lease_expires_at", "attempts"))
    return True


def _finish_work_item(item_id, token, *, status):
    with transaction.atomic():
        item = RefreshWorkItem.objects.select_for_update().select_related("source_run").filter(
            pk=item_id, status=RefreshWorkItem.Status.RUNNING, lease_token=token,
        ).first()
        if item is None:
            return
        item.status = status
        item.phase = RefreshWorkItem.Phase.COMPLETE
        item.finished_at = timezone.now()
        item.heartbeat_at = item.finished_at
        item.lease_token = ""
        item.lease_expires_at = None
        item.listings = []
        item.save(update_fields=("status", "phase", "finished_at", "heartbeat_at", "lease_token", "lease_expires_at", "listings"))
        run_status = (
            OperationalRun.Status.SUCCEEDED if status == RefreshWorkItem.Status.SUCCEEDED
            else OperationalRun.Status.PARTIAL if status == RefreshWorkItem.Status.PARTIAL
            else OperationalRun.Status.FAILED
        )
        finish_run(
            item.source_run,
            status=run_status,
            item_count=item.source_run.item_count,
            new_count=item.source_run.new_count,
            known_count=item.source_run.known_count,
            known_updated_count=item.source_run.known_updated_count,
            known_unchanged_count=item.source_run.known_unchanged_count,
            listing_count=item.listing_count,
            title_kept_count=item.title_kept_count,
            title_discarded_count=item.title_discarded_count,
            details_requested_count=item.details_requested_count,
            details_received_count=item.details_received_count,
            title_input_tokens=item.title_input_tokens,
            error_category=item.error_category if run_status != OperationalRun.Status.SUCCEEDED else "",
        )
        JobSourceStatus.objects.update_or_create(
            source=item.source,
            defaults={
                "available": item.available and status == RefreshWorkItem.Status.SUCCEEDED,
                "status_message": "" if item.available else "La consulta a la fuente fue parcial.",
                "last_checked_at": item.finished_at,
                "last_success_at": item.finished_at if item.available else item.source_run.finished_at,
                "last_vacancy_count": item.source_run.item_count,
            },
        )
    for profile_id in item.profile_links.values_list("batch_profile_id", flat=True):
        _finish_batch_profile(profile_id, failed=status != RefreshWorkItem.Status.SUCCEEDED)


@shared_task(name="jobs.resumable.process_refresh_work_item")
def process_refresh_work_item(work_item_id):
    from operations.parameters import processing_is_paused

    eligible_profiles = RefreshWorkProfile.objects.filter(
        work_item_id=work_item_id,
        batch_profile__profile__owner__is_active=True,
        batch_profile__profile__search_enabled=True,
        batch_profile__profile__cv_file__gt="",
    )
    if not eligible_profiles.exists():
        claim = _claim_work_item(work_item_id)
        if claim is None:
            return {"skipped": "already_claimed_or_finished"}
        item, token = claim
        _finish_work_item(item.pk, token, status=RefreshWorkItem.Status.SUCCEEDED)
        return {"skipped": "all_profiles_search_paused"}

    if processing_is_paused():
        RefreshWorkItem.objects.filter(pk=work_item_id, status=RefreshWorkItem.Status.QUEUED).update(
            last_dispatched_at=timezone.now() - timedelta(minutes=5),
        )
        process_refresh_work_item.apply_async(args=(work_item_id,), countdown=60)
        return {"deferred": "processing_paused"}
    claim = _claim_work_item(work_item_id)
    if claim is None:
        return {"skipped": "already_claimed_or_finished"}
    item, token = claim
    has_enabled_profile = RefreshWorkProfile.objects.filter(
        work_item_id=item.pk,
        batch_profile__profile__owner__is_active=True,
        batch_profile__profile__search_enabled=True,
        batch_profile__profile__cv_file__gt="",
    ).exists()
    if not has_enabled_profile:
        _finish_work_item(item.pk, token, status=RefreshWorkItem.Status.SUCCEEDED)
        return {"skipped": "all_profiles_search_paused"}
    connector = next((item_type for item_type in _configured_connectors() if item_type.source == item.source), None)
    if connector is None:
        _record_work_failure(item, status=RefreshWorkItem.Status.FAILED, error_category="source_error")
        return {"failed": "connector_missing"}

    try:
        if item.phase == RefreshWorkItem.Phase.TITLES:
            listing_started = time.perf_counter()
            try:
                titles = connector.fetch_titles(
                    item.search_request.get("keywords", []),
                    locations=item.search_request.get("locations", []),
                    remote_ok=item.search_request.get("remote_ok", False),
                )
                available = True
            except SourcePartiallyUnavailable as exc:
                titles = exc.listings
                available = False
            listing_ms = max(0, int((time.perf_counter() - listing_started) * 1000))
            preselection_started = time.perf_counter()
            from matching.services import preselect_listing_titles
            preselected = preselect_listing_titles(titles, item.search_request.get("keywords", []))
            preselection_ms = max(0, int((time.perf_counter() - preselection_started) * 1000))
            run = OperationalRun.objects.get(pk=item.source_run_id)
            run.listing_count = len(titles)
            run.title_kept_count = len(preselected.listings)
            run.title_discarded_count = preselected.discarded_count
            run.details_requested_count = len(preselected.listings)
            run.title_input_tokens = preselected.input_tokens
            run.listing_fetch_duration_ms = listing_ms
            run.title_preselection_duration_ms = preselection_ms
            run.save(update_fields=(
                "listing_count", "title_kept_count", "title_discarded_count", "details_requested_count",
                "title_input_tokens", "listing_fetch_duration_ms", "title_preselection_duration_ms",
            ))
            item.listings = [_listing_to_json(listing) for listing in preselected.listings]
            item.listing_count = len(titles)
            item.title_kept_count = len(preselected.listings)
            item.title_discarded_count = preselected.discarded_count
            item.details_requested_count = len(preselected.listings)
            item.title_input_tokens = preselected.input_tokens
            item.available = available
            item.phase = RefreshWorkItem.Phase.DETAILS
            item.cursor = 0
            item.heartbeat_at = timezone.now()
            item.lease_expires_at = item.heartbeat_at + timedelta(seconds=WORK_LEASE_SECONDS)
            item.save(update_fields=(
                "listings", "listing_count", "title_kept_count", "title_discarded_count",
                "details_requested_count", "title_input_tokens", "available", "phase", "cursor",
                "heartbeat_at", "lease_expires_at",
            ))
            if not item.listings:
                _finish_work_item(
                    item.pk, token,
                    status=RefreshWorkItem.Status.SUCCEEDED if available else RefreshWorkItem.Status.PARTIAL,
                )
                return {"completed": True, "listings": 0}

        item.refresh_from_db()
        batch = item.listings[item.cursor:item.cursor + DETAIL_BATCH_SIZE]
        listings = [_listing_from_json(value) for value in batch]
        detail_started = time.perf_counter()
        try:
            detailed = connector.fetch_details(listings) if item.available else listings
            detail_available = item.available
        except SourcePartiallyUnavailable as exc:
            detailed = exc.listings
            detail_available = False
        detail_ms = max(0, int((time.perf_counter() - detail_started) * 1000))
        _persist_listing_chunk(item.pk, token, item.cursor, detailed, detail_ms=detail_ms, available=detail_available)

        item.refresh_from_db()
        if item.cursor < len(item.listings):
            item.status = RefreshWorkItem.Status.QUEUED
            item.lease_token = ""
            item.lease_expires_at = None
            item.last_dispatched_at = timezone.now()
            item.save(update_fields=("status", "lease_token", "lease_expires_at", "last_dispatched_at"))
            process_refresh_work_item.apply_async(args=(item.pk,))
            return {"continued": True, "cursor": item.cursor, "total": len(item.listings)}

        status = RefreshWorkItem.Status.SUCCEEDED if item.available else RefreshWorkItem.Status.PARTIAL
        item.error_category = "" if item.available else "source_partially_unavailable"
        item.save(update_fields=("error_category",))
        _finish_work_item(item.pk, token, status=status)
        return {"completed": True, "cursor": item.cursor}
    except SourceUnavailable:
        _retry_work_item(item.pk, token, "source_unavailable")
        logger.info("refresh_work_source_unavailable source=%s", item.source)
        return {"retrying": "source_unavailable"}
    except Exception as exc:
        _retry_work_item(item.pk, token, "source_error")
        logger.error("refresh_work_failed source=%s exception_type=%s", item.source, type(exc).__name__)
        return {"retrying": "source_error"}

