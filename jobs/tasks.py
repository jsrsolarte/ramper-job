import logging
from dataclasses import dataclass
from functools import partial
from time import perf_counter

from celery import shared_task
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .connectors.base import JobListing, SourcePartiallyUnavailable, SourceUnavailable
from .models import JobSourceStatus, ManualVacancySubmission
from .registry import configured_connectors
from .services import save_listings
from profiles.models import Profile
from profiles.locations import expand_locations
from operations.models import AdminCommandRun, OperationalRun
from operations.services import (
    acquire_refresh_lease,
    begin_run,
    claim_refresh_lease,
    finish_run,
    record_admin_profile_result,
    release_refresh_lease_for_retry,
    release_refresh_lease,
    start_admin_command,
)
from operations.parameters import processing_is_paused

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceFetchSummary:
    listings: list
    listing_count: int
    title_kept_count: int | None = None
    title_discarded_count: int | None = None
    details_requested_count: int | None = None
    details_received_count: int | None = None
    title_input_tokens: int | None = None
    listing_fetch_duration_ms: int | None = None
    title_preselection_duration_ms: int | None = None
    detail_fetch_duration_ms: int | None = None
    source_available: bool = True


def _elapsed_ms(started):
    return max(0, int((perf_counter() - started) * 1000))


def _record_source_fetch_outcome(connector, fetched, saved, run, checked_at):
    """Persist source availability and ingestion metrics for complete or partial fetches."""
    JobSourceStatus.objects.update_or_create(
        source=connector.source,
        defaults={
            "available": fetched.source_available,
            "status_message": getattr(connector, "status_message", "")[:300],
            "last_checked_at": checked_at,
            "last_success_at": checked_at,
            "last_vacancy_count": len(saved.vacancies),
        },
    )
    finish_run(
        run,
        status=OperationalRun.Status.SUCCEEDED if fetched.source_available else OperationalRun.Status.PARTIAL,
        item_count=len(saved.vacancies),
        new_count=saved.new_count,
        known_count=saved.known_count,
        known_updated_count=saved.known_updated_count,
        known_unchanged_count=saved.known_unchanged_count,
        listing_count=fetched.listing_count,
        title_kept_count=fetched.title_kept_count,
        title_discarded_count=fetched.title_discarded_count,
        details_requested_count=fetched.details_requested_count,
        details_received_count=fetched.details_received_count,
        title_input_tokens=fetched.title_input_tokens,
        listing_fetch_duration_ms=fetched.listing_fetch_duration_ms,
        title_preselection_duration_ms=fetched.title_preselection_duration_ms,
        detail_fetch_duration_ms=fetched.detail_fetch_duration_ms,
        error_category="" if fetched.source_available else "source_partially_unavailable",
        error_summary="" if fetched.source_available else getattr(connector, "status_message", "")[:240],
    )


def _fetch_source_listings(connector, keywords, locations, *, remote_ok):
    """Run title preselection when a connector supports separate search/detail phases."""
    if not callable(getattr(type(connector), "fetch_titles", None)) or not callable(
        getattr(type(connector), "fetch_details", None)
    ):
        listings = connector.fetch(keywords, locations=locations, remote_ok=remote_ok)
        return SourceFetchSummary(
            listings=listings,
            listing_count=len(listings),
            details_requested_count=len(listings),
            details_received_count=len(listings),
        )

    fetch_titles = connector.fetch_titles
    fetch_details = connector.fetch_details
    from matching.services import preselect_listing_titles

    listing_started = perf_counter()
    try:
        title_listings = fetch_titles(keywords, locations=locations, remote_ok=remote_ok)
    except SourcePartiallyUnavailable as exc:
        listing_fetch_duration_ms = _elapsed_ms(listing_started)
        preselection_started = perf_counter()
        result = preselect_listing_titles(exc.listings, keywords)
        title_preselection_duration_ms = _elapsed_ms(preselection_started)
        logger.info(
            "vacancy_title_preselection source=%s titles=%s discarded=%s details_requested=0 input_tokens=%s",
            connector.source,
            len(exc.listings),
            result.discarded_count,
            result.input_tokens if result.input_tokens is not None else "unknown",
        )
        return SourceFetchSummary(
            listings=result.listings,
            listing_count=len(exc.listings),
            title_kept_count=len(result.listings),
            title_discarded_count=result.discarded_count,
            details_requested_count=0,
            details_received_count=0,
            title_input_tokens=result.input_tokens,
            listing_fetch_duration_ms=listing_fetch_duration_ms,
            title_preselection_duration_ms=title_preselection_duration_ms,
            detail_fetch_duration_ms=0,
            source_available=False,
        )
    listing_fetch_duration_ms = _elapsed_ms(listing_started)
    preselection_started = perf_counter()
    result = preselect_listing_titles(title_listings, keywords)
    title_preselection_duration_ms = _elapsed_ms(preselection_started)
    detail_started = perf_counter()
    source_available = True
    try:
        detailed_listings = fetch_details(result.listings)
    except SourcePartiallyUnavailable as exc:
        detailed_listings = exc.listings
        source_available = False
    detail_fetch_duration_ms = _elapsed_ms(detail_started)
    logger.info(
        "vacancy_title_preselection source=%s titles=%s discarded=%s details_requested=%s input_tokens=%s",
        connector.source,
        len(title_listings),
        result.discarded_count,
        len(result.listings),
        result.input_tokens if result.input_tokens is not None else "unknown",
    )
    return SourceFetchSummary(
        listings=detailed_listings,
        listing_count=len(title_listings),
        title_kept_count=len(result.listings),
        title_discarded_count=result.discarded_count,
        details_requested_count=len(result.listings),
        details_received_count=len(detailed_listings),
        title_input_tokens=result.input_tokens,
        listing_fetch_duration_ms=listing_fetch_duration_ms,
        title_preselection_duration_ms=title_preselection_duration_ms,
        detail_fetch_duration_ms=detail_fetch_duration_ms,
        source_available=source_available,
    )


def _refresh_profile_sources(profile):
    from matching.services import get_active_matching_config, get_profile_search_terms
    from matching.tasks import schedule_vacancy_analysis

    revision = profile.revisions.filter(version=profile.revision_number).first()
    if revision is None or not profile.cv_file:
        return []

    config = get_active_matching_config()
    search_terms = get_profile_search_terms(revision, config)
    results = []
    for connector in configured_connectors():
        checked_at = timezone.now()
        run = begin_run(
            kind=OperationalRun.Kind.INGESTION,
            operation="source_query",
            source=connector.source,
        )
        try:
            locations = expand_locations(revision.locations)
            fetched = _fetch_source_listings(
                connector, search_terms.keywords, locations, remote_ok=revision.remote_ok,
            )
            saved = save_listings(fetched.listings)
            vacancies = saved.vacancies
            from matching.models import ProfileVacancyDiscovery
            ProfileVacancyDiscovery.objects.bulk_create(
                [
                    ProfileVacancyDiscovery(
                        profile=profile,
                        vacancy=vacancy,
                        auto_discard_threshold=profile.min_score or 0,
                    )
                    for vacancy in vacancies
                ],
                ignore_conflicts=True,
            )
            for vacancy in vacancies:
                if getattr(vacancy, "_materially_changed", True):
                    transaction.on_commit(partial(
                        schedule_vacancy_analysis.delay,
                        vacancy.pk,
                        force_reanalysis=True,
                        source_query_run_ids_by_profile={str(profile.pk): [run.pk]},
                    ))
        except SourceUnavailable as exc:
            status_message = str(exc)[:300]
            JobSourceStatus.objects.update_or_create(
                source=connector.source,
                defaults={"available": False, "status_message": status_message, "last_checked_at": checked_at},
            )
            logger.info("La fuente %s no está disponible para consulta pública.", connector.source)
            finish_run(run, status=OperationalRun.Status.FAILED, error_category="source_unavailable")
            results.append({"source": connector.source, "available": False, "count": 0})
            continue
        except Exception as exc:
            finish_run(run, status=OperationalRun.Status.FAILED, error_category="source_error")
            logger.error("source_query_failed source=%s exception_type=%s", connector.source, type(exc).__name__)
            raise

        _record_source_fetch_outcome(connector, fetched, saved, run, checked_at)
        results.append({"source": connector.source, "available": fetched.source_available, "count": len(vacancies)})
    return results


@shared_task(bind=True, name="jobs.tasks.refresh_profile_sources", max_retries=3)
def refresh_profile_sources(self, profile_id, command_run_id=None, lease_token=None):
    from matching.client import OmniRouteError

    if processing_is_paused():
        if lease_token:
            release_refresh_lease(f"profile-refresh:{profile_id}", lease_token)
        refresh_profile_sources.apply_async(
            args=(profile_id,),
            kwargs={"command_run_id": command_run_id},
            countdown=60,
        )
        return {"deferred": "processing_paused"}

    lease_key = f"profile-refresh:{profile_id}"
    if lease_token:
        claimed = claim_refresh_lease(lease_key, lease_token)
    else:
        lease_token = acquire_refresh_lease(lease_key)
        claimed = bool(lease_token and claim_refresh_lease(lease_key, lease_token))
    if not claimed:
        if command_run_id:
            record_admin_profile_result(command_run_id, results=[])
        return {"skipped": "already_running"}

    keep_lease = False
    try:
        profile = get_object_or_404(
            Profile.objects.select_related("owner"),
            pk=profile_id,
            owner__is_active=True,
        )
    except Exception:
        release_refresh_lease(lease_key, lease_token)
        if command_run_id:
            record_admin_profile_result(command_run_id, failed=True)
        raise
    run = begin_run(
        kind=OperationalRun.Kind.INGESTION,
        operation="profile_refresh",
        task_id=self.request.id or "",
    )
    try:
        try:
            results = _refresh_profile_sources(profile)
        except OmniRouteError as exc:
            will_retry = self.request.retries < self.max_retries
            finish_run(
                run,
                status=OperationalRun.Status.RETRYING if will_retry else OperationalRun.Status.FAILED,
                error_category=exc.category,
            )
            logger.warning("profile_refresh_failed category=%s will_retry=%s", exc.category, will_retry)
            if will_retry:
                release_refresh_lease_for_retry(lease_key, lease_token)
                keep_lease = True
                raise self.retry(exc=exc, countdown=60)
            if command_run_id:
                record_admin_profile_result(command_run_id, failed=True)
            raise
        except Exception as exc:
            finish_run(run, status=OperationalRun.Status.FAILED, error_category="source_error")
            logger.error("profile_refresh_failed exception_type=%s", type(exc).__name__)
            if command_run_id:
                record_admin_profile_result(command_run_id, failed=True)
            raise
        else:
            finish_run(
                run,
                status=OperationalRun.Status.SUCCEEDED,
                item_count=sum(result["count"] for result in results),
            )
            if command_run_id:
                record_admin_profile_result(command_run_id, results=results)
            return results
    finally:
        if not keep_lease:
            release_refresh_lease(lease_key, lease_token)


@shared_task(name="jobs.tasks.refresh_shared_sources")
def refresh_shared_sources(profile_leases, command_run_id=None):
    """Query each equivalent profile/source request once, then fan results out safely."""
    from matching.client import OmniRouteError
    from matching.models import MatchingConfig
    from matching.services import get_active_matching_config, get_profile_search_terms
    from matching.tasks import schedule_vacancy_analysis
    from profiles.locations import vacancy_location_is_eligible

    from .search_groups import group_search_requests

    if processing_is_paused():
        for profile_id_value, token in (profile_leases or {}).items():
            release_refresh_lease(f"profile-refresh:{int(profile_id_value)}", token)
        refresh_sources.apply_async(kwargs={"command_run_id": command_run_id}, countdown=60)
        return {"deferred": "processing_paused"}

    claimed = {}
    profile_runs = {}
    reports = {}
    query_reports = []
    report_failures = set()
    fallback_profiles = set()
    stale_profiles = set()
    profile_objects = {}
    requests = []
    found_by_profile = {}
    vacancy_targets = {}
    query_group_count = 0

    def defer_after_current_query():
        for profile_id, run in profile_runs.items():
            if run.finished_at is None:
                finish_run(
                    run,
                    status=OperationalRun.Status.PARTIAL,
                    item_count=len(found_by_profile.get(profile_id, set())),
                )
        refresh_sources.apply_async(kwargs={"command_run_id": command_run_id}, countdown=60)
        return {"deferred": "processing_paused"}

    for profile_id_value, token in (profile_leases or {}).items():
        profile_id = int(profile_id_value)
        lease_key = f"profile-refresh:{profile_id}"
        if not claim_refresh_lease(lease_key, token):
            if command_run_id:
                record_admin_profile_result(command_run_id, results=[])
            continue
        claimed[profile_id] = token

    try:
        config = get_active_matching_config()
        for profile_id in claimed:
            profile = Profile.objects.select_related("owner").filter(
                pk=profile_id, owner__is_active=True, cv_file__gt="", revision_number__gt=0,
            ).first()
            if profile is None:
                continue
            revision = profile.revisions.filter(version=profile.revision_number).first()
            if revision is None:
                continue
            profile_objects[profile_id] = profile
            profile_runs[profile_id] = begin_run(
                kind=OperationalRun.Kind.INGESTION,
                operation="profile_refresh",
            )
            try:
                terms = get_profile_search_terms(revision, config)
            except OmniRouteError as exc:
                finish_run(
                    profile_runs[profile_id],
                    status=OperationalRun.Status.RETRYING,
                    error_category=exc.category,
                )
                fallback_profiles.add(profile_id)
                continue
            except Exception as exc:
                finish_run(
                    profile_runs[profile_id],
                    status=OperationalRun.Status.FAILED,
                    error_category="search_terms_error",
                )
                report_failures.add(profile_id)
                logger.error("profile_search_terms_failed exception_type=%s", type(exc).__name__)
                continue

            requests.append({
                "profile_id": profile_id,
                "revision_id": revision.pk,
                "matching_config_id": config.pk,
                "keywords": list(terms.keywords),
                "locations": expand_locations(revision.locations),
                "remote_ok": revision.remote_ok,
            })

        for connector in configured_connectors():
            if processing_is_paused():
                return defer_after_current_query()
            groups = group_search_requests(connector, requests)
            query_group_count += len(groups)
            for group in groups:
                if processing_is_paused():
                    return defer_after_current_query()
                request = group["request"]
                members = group["members"]
                current_config_id = MatchingConfig.objects.filter(is_active=True).order_by(
                    "-version"
                ).values_list("pk", flat=True).first()
                if current_config_id != request["matching_config_id"]:
                    stale_profiles.update(member["profile_id"] for member in members)
                    continue

                valid_members = []
                for member in members:
                    profile = Profile.objects.select_related("owner").filter(
                        pk=member["profile_id"], owner__is_active=True, cv_file__gt="",
                    ).first()
                    revision = profile.revisions.filter(
                        pk=member["revision_id"], version=profile.revision_number,
                    ).first() if profile else None
                    if profile and revision:
                        valid_members.append((member, profile, revision))
                    elif profile and profile.cv_file:
                        stale_profiles.add(member["profile_id"])
                if not valid_members:
                    continue

                checked_at = timezone.now()
                run = begin_run(
                    kind=OperationalRun.Kind.INGESTION,
                    operation="source_query",
                    source=connector.source,
                )
                try:
                    fetched = _fetch_source_listings(
                        connector,
                        request["keywords"],
                        request["locations"],
                        remote_ok=request["remote_ok"],
                    )
                    saved = save_listings(fetched.listings)
                    vacancies = saved.vacancies
                except SourceUnavailable as exc:
                    status_message = str(exc)[:300]
                    JobSourceStatus.objects.update_or_create(
                        source=connector.source,
                        defaults={"available": False, "status_message": status_message, "last_checked_at": checked_at},
                    )
                    finish_run(run, status=OperationalRun.Status.FAILED, error_category="source_unavailable")
                    query_reports.append((
                        [member[0]["profile_id"] for member in valid_members],
                        {"source": connector.source, "available": False, "count": 0},
                    ))
                    logger.info("La fuente %s no está disponible para consulta pública.", connector.source)
                    continue
                except Exception as exc:
                    finish_run(run, status=OperationalRun.Status.FAILED, error_category="source_error")
                    query_reports.append((
                        [member[0]["profile_id"] for member in valid_members],
                        {"source": connector.source, "available": False, "count": 0},
                    ))
                    report_failures.update(member[0]["profile_id"] for member in valid_members)
                    logger.error(
                        "shared_source_query_failed source=%s exception_type=%s",
                        connector.source,
                        type(exc).__name__,
                    )
                    continue

                _record_source_fetch_outcome(connector, fetched, saved, run, checked_at)

                post_valid_members = []
                current_config_id = MatchingConfig.objects.filter(is_active=True).order_by(
                    "-version"
                ).values_list("pk", flat=True).first()
                if current_config_id != request["matching_config_id"]:
                    stale_profiles.update(member[0]["profile_id"] for member in valid_members)
                    continue
                for member, _profile, _revision in valid_members:
                    fresh_profile = Profile.objects.select_related("owner").filter(
                        pk=member["profile_id"], owner__is_active=True, cv_file__gt="",
                    ).first()
                    fresh_revision = fresh_profile.revisions.filter(
                        pk=member["revision_id"], version=fresh_profile.revision_number,
                    ).first() if fresh_profile else None
                    if fresh_revision is None:
                        if fresh_profile:
                            stale_profiles.add(member["profile_id"])
                        continue
                    post_valid_members.append((member, fresh_profile, fresh_revision))
                if not post_valid_members:
                    continue
                query_reports.append((
                    [member[0]["profile_id"] for member in post_valid_members],
                        {"source": connector.source, "available": fetched.source_available, "count": len(vacancies)},
                ))

                for vacancy in vacancies:
                    target = vacancy_targets.setdefault(vacancy.pk, {
                        "profile_revisions": {},
                        "source_query_run_ids_by_profile": {},
                        "materially_changed": False,
                    })
                    target["materially_changed"] = (
                        target["materially_changed"] or getattr(vacancy, "_materially_changed", False)
                    )
                    for member, _profile, revision in post_valid_members:
                        if not vacancy_location_is_eligible(vacancy, revision):
                            continue
                        profile_id = member["profile_id"]
                        target["profile_revisions"][str(profile_id)] = member["revision_id"]
                        target["source_query_run_ids_by_profile"].setdefault(str(profile_id), set()).add(run.pk)
                        found_by_profile.setdefault(profile_id, set()).add(vacancy.pk)

        if processing_is_paused():
            return defer_after_current_query()

        active_config_id = MatchingConfig.objects.filter(is_active=True).order_by(
            "-version"
        ).values_list("pk", flat=True).first()
        for request in requests:
            profile_id = request["profile_id"]
            if active_config_id != request["matching_config_id"]:
                stale_profiles.add(profile_id)
                continue
            profile = Profile.objects.select_related("owner").filter(
                pk=profile_id, owner__is_active=True, cv_file__gt="",
            ).first()
            current_revision_id = profile.revisions.filter(
                version=profile.revision_number,
            ).values_list("pk", flat=True).first() if profile else None
            if profile and current_revision_id != request["revision_id"]:
                stale_profiles.add(profile_id)

        for member_ids, result in query_reports:
            eligible_reporters = [
                profile_id for profile_id in member_ids
                if profile_id in claimed and profile_id not in stale_profiles
            ]
            if eligible_reporters:
                reports.setdefault(eligible_reporters[0], []).append(result)

        for vacancy_id, target in vacancy_targets.items():
            profile_revisions = target["profile_revisions"]
            profile_revisions = {
                profile_id: revision_id
                for profile_id, revision_id in profile_revisions.items()
                if int(profile_id) not in stale_profiles
            }
            if not profile_revisions:
                continue
            try:
                schedule_vacancy_analysis.delay(
                    vacancy_id,
                    force_reanalysis=target["materially_changed"],
                    profile_ids=[int(profile_id) for profile_id in profile_revisions],
                    expected_revision_ids=profile_revisions,
                    expected_matching_config_id=request["matching_config_id"],
                    source_query_run_ids_by_profile={
                        profile_id: sorted(run_ids)
                        for profile_id, run_ids in target["source_query_run_ids_by_profile"].items()
                        if profile_id in profile_revisions
                    },
                )
            except Exception as exc:
                report_failures.update(int(profile_id) for profile_id in profile_revisions)
                logger.error(
                    "shared_vacancy_fanout_failed vacancy_id=%s exception_type=%s",
                    vacancy_id,
                    type(exc).__name__,
                )

        for profile_id, run in profile_runs.items():
            if run.status in (OperationalRun.Status.FAILED, OperationalRun.Status.RETRYING):
                continue
            finish_run(
                run,
                status=OperationalRun.Status.SUCCEEDED,
                item_count=len(found_by_profile.get(profile_id, set())),
            )
    finally:
        for profile_id, token in claimed.items():
            release_refresh_lease(f"profile-refresh:{profile_id}", token)

    reschedule = fallback_profiles | stale_profiles
    for profile_id in claimed:
        if profile_id in reschedule:
            try:
                refresh_profile_sources.delay(profile_id, command_run_id=command_run_id)
            except Exception as exc:
                report_failures.add(profile_id)
                if command_run_id:
                    record_admin_profile_result(command_run_id, results=[], failed=True)
                logger.error("profile_refresh_reschedule_failed exception_type=%s", type(exc).__name__)
            continue
        if command_run_id:
            record_admin_profile_result(
                command_run_id,
                results=reports.get(profile_id, []),
                failed=profile_id in report_failures,
            )
    return {"refreshed_profiles": len(claimed), "shared_search_groups": query_group_count}


@shared_task(name="jobs.tasks.refresh_sources")
def refresh_sources(command_run_id=None):
    if processing_is_paused():
        refresh_sources.apply_async(kwargs={"command_run_id": command_run_id}, countdown=60)
        return {"deferred": "processing_paused"}
    profiles = Profile.objects.filter(
        owner__is_active=True,
        cv_file__gt="",
        revision_number__gt=0,
    )
    profile_ids = list(profiles.values_list("pk", flat=True))
    if command_run_id:
        start_admin_command(command_run_id, len(profile_ids))
        if not profile_ids:
            record_admin_profile_result(command_run_id, results=[])
            return {"scheduled_profiles": 0}
    profile_leases = {}
    for profile_id in profile_ids:
        lease_key = f"profile-refresh:{profile_id}"
        lease_token = acquire_refresh_lease(lease_key)
        if not lease_token:
            if command_run_id:
                record_admin_profile_result(command_run_id, results=[])
            continue
        profile_leases[str(profile_id)] = lease_token
    if profile_leases:
        try:
            refresh_shared_sources.delay(profile_leases, command_run_id=command_run_id)
        except Exception:
            for profile_id, lease_token in profile_leases.items():
                release_refresh_lease(f"profile-refresh:{profile_id}", lease_token)
                if command_run_id:
                    record_admin_profile_result(command_run_id, failed=True)
            if not command_run_id:
                raise
    return {"scheduled_profiles": len(profile_leases)}


@shared_task(name="jobs.tasks.process_manual_vacancy_submission")
def process_manual_vacancy_submission(submission_id):
    """Extract a public vacancy URL and asynchronously schedule profile analysis."""
    if processing_is_paused():
        process_manual_vacancy_submission.apply_async(args=(submission_id,), countdown=60)
        return {"deferred": "processing_paused"}
    claimed = ManualVacancySubmission.objects.filter(
        pk=submission_id,
        status=ManualVacancySubmission.Status.QUEUED,
    ).update(status=ManualVacancySubmission.Status.PROCESSING, updated_at=timezone.now())
    if not claimed:
        return {"skipped": "already_processed"}

    submission = ManualVacancySubmission.objects.filter(pk=submission_id).first()
    if submission is None:
        return {"skipped": "missing_submission"}

    try:
        from .connectors.elempleo import resolve_vacancy_url_provider

        connector = resolve_vacancy_url_provider(submission.original_url)
        listing = connector.fetch_vacancy_url(submission.original_url)
        submission.title = listing.title
        submission.source = listing.source
        submission.company = listing.company or ""
        submission.location = listing.location or ""
        submission.description = listing.description or ""
        submission.salary = listing.salary or ""
        submission.contract_type = listing.contract_type or ""
        submission.modality = (listing.raw_data.get("details") or {}).get("modality") or ""
        listing = JobListing(
            source=listing.source,
            external_id=listing.external_id,
            title=listing.title,
            company=listing.company,
            location=listing.location,
            description=listing.description,
            original_url=listing.original_url,
            raw_data={
                **(listing.raw_data or {}),
                "manual_submission": True,
            },
            salary=listing.salary,
            contract_type=listing.contract_type,
        )
        from .services import save_listing
        from matching.tasks import schedule_vacancy_analysis

        vacancy, created = save_listing(listing)
        materially_changed = getattr(vacancy, "_materially_changed", created)
        schedule_vacancy_analysis.delay(vacancy.pk, force_reanalysis=materially_changed)
    except Exception as exc:
        submission.status = ManualVacancySubmission.Status.FAILED
        submission.result_message = (
            "No fue posible guardar la vacante o programar el análisis. Puedes volver a enviarla para reintentar."
        )
        submission.save(update_fields=("status", "result_message", "updated_at"))
        logger.error(
            "manual_vacancy_submission_failed submission_id=%s exception_type=%s",
            submission.pk,
            type(exc).__name__,
        )
        return {"status": submission.status}

    submission.vacancy = vacancy
    submission.status = ManualVacancySubmission.Status.SCHEDULED
    if created:
        submission.result_message = "Vacante nueva guardada; análisis programado para perfiles elegibles."
    elif materially_changed:
        submission.result_message = "Vacante existente actualizada; análisis programado para perfiles elegibles."
    else:
        submission.result_message = "Vacante existente reutilizada; se conservaron los análisis completados."
    submission.save(update_fields=(
        "vacancy", "status", "result_message", "title", "source", "company", "location",
        "modality", "description", "salary", "contract_type", "updated_at",
    ))
    return {"status": submission.status, "vacancy_id": vacancy.pk, "created": created}


