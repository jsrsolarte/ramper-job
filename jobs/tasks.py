import logging

from celery import shared_task
from django.utils import timezone

from .connectors.base import JobListing
from .registry import configured_connectors  # compatibility for callers patching the task module
from .models import ManualVacancySubmission
from profiles.models import Profile
from operations.models import AdminCommandRun
from operations.services import (
    acquire_refresh_lease,
    claim_refresh_lease,
    record_admin_profile_result,
    release_refresh_lease,
    start_admin_command,
)
from operations.parameters import processing_is_paused

logger = logging.getLogger(__name__)


@shared_task(name="jobs.tasks.refresh_profile_sources")
def refresh_profile_sources(profile_id, command_run_id=None, lease_token=None):
    """Schedule one profile through the same bounded, resumable pipeline as bulk refreshes."""
    from .resumable import prepare_refresh_batch
    from operations.services import renew_refresh_lease

    profile_is_searchable = Profile.objects.filter(
        pk=profile_id,
        owner__is_active=True,
        search_enabled=True,
        cv_file__gt="",
        revision_number__gt=0,
    ).exists()
    if not profile_is_searchable:
        if lease_token:
            release_refresh_lease(f"profile-refresh:{profile_id}", lease_token)
        return {"skipped": "profile_search_paused_or_incomplete"}

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
    if not lease_token:
        lease_token = acquire_refresh_lease(lease_key)
    if not lease_token or not claim_refresh_lease(lease_key, lease_token):
        return {"skipped": "already_running"}
    renew_refresh_lease(lease_key, lease_token, ttl_seconds=24 * 60 * 60)
    try:
        prepare_refresh_batch.delay(
            {str(profile_id): lease_token},
            command_run_id=command_run_id,
            leases_already_claimed=True,
        )
    except Exception:
        release_refresh_lease(lease_key, lease_token)
        raise
    return {"scheduled_profiles": 1}


@shared_task(name="jobs.tasks.refresh_shared_sources")
def refresh_shared_sources(profile_leases, command_run_id=None):
    """Compatibility entry point for queued jobs; route them through resumable work."""
    from .resumable import prepare_refresh_batch

    prepare_refresh_batch.delay(profile_leases, command_run_id=command_run_id)
    return {"scheduled_profiles": len(profile_leases or {})}


@shared_task(name="jobs.tasks.refresh_sources")
def refresh_sources(command_run_id=None):
    if processing_is_paused():
        refresh_sources.apply_async(kwargs={"command_run_id": command_run_id}, countdown=60)
        return {"deferred": "processing_paused"}
    profiles = Profile.objects.filter(
        owner__is_active=True,
        search_enabled=True,
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


@shared_task(name="jobs.tasks.refresh_periodic_sources")
def refresh_periodic_sources():
    """Mark and run only the global automatic source-refresh cycle scheduled by Celery Beat."""
    if not processing_is_paused():
        from operations.scheduling import record_periodic_refresh_start

        record_periodic_refresh_start()
    return refresh_sources()


# Register the resumable worker tasks with Celery's task autodiscovery.
from . import resumable as _resumable_tasks  # noqa: E402,F401


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


