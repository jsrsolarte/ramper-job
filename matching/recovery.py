import logging
from datetime import timedelta
from functools import partial

from django.conf import settings
from django.db import transaction
from django.db.models import F, Q, OuterRef, Subquery
from django.utils import timezone

from matching.models import ProfileVacancyDiscovery, VacancyAnalysis
from matching.services import get_active_matching_config
from operations.models import OperationalRun
from operations.services import begin_run, finish_run
from profiles.locations import vacancy_location_is_eligible

logger = logging.getLogger(__name__)


def expire_discovery_if_due(discovery, profile, vacancy, now):
    from dashboard.models import VacancyFollowUp
    from dashboard.services import discard_follow_up
    from operations.parameters import current_auto_discard_days

    if discovery.first_found_at + timedelta(days=current_auto_discard_days()) > now:
        return False
    follow_up = VacancyFollowUp.objects.select_for_update().filter(profile=profile, vacancy=vacancy).first()
    completed = VacancyAnalysis.objects.filter(
        profile=profile, vacancy=vacancy, status=VacancyAnalysis.Status.COMPLETED,
        profile_revision__version=profile.revision_number,
    ).exists()
    if not completed and (follow_up is None or follow_up.status == VacancyFollowUp.Status.PENDING):
        discard_follow_up(profile, vacancy, now=now)
    return True


def _dispatch_analysis(analysis_id):
    from matching.tasks import analyze_vacancy_for_profile

    analyze_vacancy_for_profile.delay(analysis_id)


def enqueue_analysis(analysis_id, *, force=False):
    """Persist an analysis dispatch before publishing it to Celery."""
    now = timezone.now()
    with transaction.atomic():
        analysis = VacancyAnalysis.objects.select_for_update().filter(pk=analysis_id).first()
        if analysis is None or analysis.status != VacancyAnalysis.Status.PENDING:
            return False
        if analysis.processing_started_at and analysis.processing_started_at > now - timedelta(
            seconds=settings.ANALYSIS_RECOVERY_LEASE_SECONDS
        ):
            return False
        if not force and analysis.last_enqueued_at and analysis.last_enqueued_at > now - timedelta(
            seconds=settings.ANALYSIS_RECOVERY_STALE_SECONDS
        ):
            return False
        analysis.last_enqueued_at = now
        if analysis.processing_started_at:
            analysis.processing_started_at = None
        analysis.save(update_fields=("last_enqueued_at", "processing_started_at", "updated_at"))
        transaction.on_commit(partial(_dispatch_analysis, analysis.pk))
    return True


def claim_analysis(analysis_id):
    """Acquire the per-analysis worker lease, or return None for a duplicate."""
    now = timezone.now()
    lease_cutoff = now - timedelta(seconds=settings.ANALYSIS_RECOVERY_LEASE_SECONDS)
    with transaction.atomic():
        analysis = (
            VacancyAnalysis.objects.select_for_update()
            .select_related("profile", "profile_revision", "vacancy", "matching_config")
            .filter(pk=analysis_id)
            .first()
        )
        if analysis is None or analysis.status != VacancyAnalysis.Status.PENDING:
            return None
        if analysis.processing_started_at and analysis.processing_started_at >= lease_cutoff:
            return None
        if (
            analysis.profile_revision.version != analysis.profile.revision_number
            or not analysis.vacancy.is_active
            or not analysis.profile.owner.is_active
            or not analysis.profile.cv_file
            or not vacancy_location_is_eligible(analysis.vacancy, analysis.profile_revision)
        ):
            return None
        discovery, _ = ProfileVacancyDiscovery.objects.get_or_create(
            profile=analysis.profile, vacancy=analysis.vacancy,
            defaults={
                "first_found_at": analysis.created_at,
                "auto_discard_threshold": analysis.profile.min_score or 0,
            },
        )
        if expire_discovery_if_due(discovery, analysis.profile, analysis.vacancy, now):
            analysis.status = VacancyAnalysis.Status.SUPERSEDED
            analysis.error_message = "Venció el plazo de análisis para este perfil."
            analysis.processing_started_at = None
            analysis.save(update_fields=("status", "error_message", "processing_started_at", "updated_at"))
            return None
        analysis.processing_started_at = now
        analysis.save(update_fields=("processing_started_at", "updated_at"))
    return analysis


def release_analysis(analysis_id, *, error_message="", update_dispatch=False):
    values = {
        "processing_started_at": None,
        "error_message": error_message,
        "updated_at": timezone.now(),
    }
    if update_dispatch:
        values["last_enqueued_at"] = timezone.now()
    VacancyAnalysis.objects.filter(
        pk=analysis_id,
        status=VacancyAnalysis.Status.PENDING,
    ).update(**values)


def reconcile_pending_analyses(batch_size=None):
    """Requeue stale eligible work and expire discoveries past their deadline."""
    now = timezone.now()
    batch_size = max(1, int(batch_size or settings.ANALYSIS_RECOVERY_BATCH_SIZE))
    stale_seconds = settings.ANALYSIS_RECOVERY_STALE_SECONDS
    lease_cutoff = now - timedelta(seconds=settings.ANALYSIS_RECOVERY_LEASE_SECONDS)
    candidate_limit = batch_size * 4
    config = get_active_matching_config()
    latest = VacancyAnalysis.objects.filter(
        profile_id=OuterRef("profile_id"), vacancy_id=OuterRef("vacancy_id"),
        profile_revision_id=OuterRef("profile_revision_id"), matching_config_id=OuterRef("matching_config_id"),
    ).order_by("-created_at", "-pk").values("pk")[:1]
    candidates = list(
        VacancyAnalysis.objects.filter(
            status__in=[VacancyAnalysis.Status.PENDING, VacancyAnalysis.Status.FAILED],
            profile_revision__version=F("profile__revision_number"),
            profile__owner__is_active=True,
            profile__cv_file__gt="",
            vacancy__is_active=True,
            matching_config=config,
        )
        .annotate(latest_id=Subquery(latest)).filter(pk=F("latest_id"))
        .filter(Q(processing_started_at__isnull=True) | Q(processing_started_at__lt=lease_cutoff))
        .select_related("profile", "profile_revision", "vacancy")
        .order_by("created_at")[:candidate_limit]
    )

    recovered = 0
    exhausted = 0
    for candidate in candidates:
        if recovered + exhausted >= batch_size:
            break
        if not vacancy_location_is_eligible(candidate.vacancy, candidate.profile_revision):
            continue
        dispatch = False
        terminalize = False
        with transaction.atomic():
            analysis = VacancyAnalysis.objects.select_for_update().filter(pk=candidate.pk).first()
            if (
                analysis is None
                or analysis.status not in (VacancyAnalysis.Status.PENDING, VacancyAnalysis.Status.FAILED)
                or analysis.profile_revision.version != analysis.profile.revision_number
                or not analysis.vacancy.is_active
                or analysis.matching_config_id != config.pk
                or not analysis.profile.owner.is_active
                or not analysis.profile.cv_file
                or not vacancy_location_is_eligible(analysis.vacancy, analysis.profile_revision)
            ):
                continue
            lease_stale = bool(analysis.processing_started_at and analysis.processing_started_at < lease_cutoff)
            if analysis.processing_started_at and not lease_stale:
                continue
            discovery, _ = ProfileVacancyDiscovery.objects.get_or_create(
                profile=analysis.profile, vacancy=analysis.vacancy,
                defaults={
                    "first_found_at": analysis.created_at,
                    "auto_discard_threshold": analysis.profile.min_score or 0,
                },
            )
            if expire_discovery_if_due(discovery, analysis.profile, analysis.vacancy, now):
                analysis.status = VacancyAnalysis.Status.SUPERSEDED
                analysis.processing_started_at = None
                analysis.error_message = "Venció el plazo de análisis para este perfil."
                analysis.save(update_fields=("status", "processing_started_at", "error_message", "updated_at"))
                terminalize = True
            else:
                last_dispatch = analysis.last_enqueued_at or analysis.created_at
                delay_seconds = min(3600, stale_seconds * (2 ** min(analysis.recovery_count, 12)))
                if not lease_stale and last_dispatch > now - timedelta(seconds=delay_seconds):
                    continue
                analysis.status = VacancyAnalysis.Status.PENDING
                analysis.recovery_count = min(32767, analysis.recovery_count + 1)
                analysis.last_enqueued_at = now
                analysis.processing_started_at = None
                analysis.save(update_fields=("status", "recovery_count", "last_enqueued_at", "processing_started_at", "updated_at"))
                transaction.on_commit(partial(_dispatch_analysis, analysis.pk))
                dispatch = True
        if dispatch:
            recovered += 1
        if terminalize:
            exhausted += 1

    if recovered:
        run = begin_run(
            kind=OperationalRun.Kind.RECOVERY,
            operation="analysis_recovery",
        )
        finish_run(run, status=OperationalRun.Status.SUCCEEDED, item_count=recovered)
    if exhausted:
        run = begin_run(
            kind=OperationalRun.Kind.RECOVERY,
            operation="analysis_recovery_expired",
        )
        finish_run(
            run,
            status=OperationalRun.Status.FAILED,
            item_count=exhausted,
            error_category="analysis.expired",
        )
    logger.info("analysis_reconciliation recovered=%s exhausted=%s", recovered, exhausted)
    return {"recovered": recovered, "exhausted": exhausted}
