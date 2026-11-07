import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from dashboard.services import discard_follow_up
from matching.models import RUBRIC_VERSION, VacancyAnalysis
from profiles.locations import vacancy_location_is_eligible
from profiles.models import Profile
from operations.parameters import (
    DEFAULT_AUTO_DISCARD_DAYS,
    DEFAULT_FOLLOW_UP_ARCHIVE_DAYS,
    current_auto_discard_days,
    current_follow_up_archive_days,
)

logger = logging.getLogger(__name__)


@shared_task(name="dashboard.tasks.discard_stale_recommendations")
def discard_stale_recommendations(retention_days=None):
    """Discard pending recommendations after their profile-specific age reaches the limit."""
    if retention_days is None:
        retention_days = current_auto_discard_days()
    else:
        try:
            retention_days = int(retention_days)
        except (TypeError, ValueError):
            retention_days = DEFAULT_AUTO_DISCARD_DAYS
        if not 1 <= retention_days <= 365:
            retention_days = DEFAULT_AUTO_DISCARD_DAYS
    now = timezone.now()
    cutoff = now - timedelta(days=retention_days)
    latest_result = VacancyAnalysis.objects.filter(
        profile=OuterRef("profile"),
        vacancy=OuterRef("vacancy"),
        status=VacancyAnalysis.Status.COMPLETED,
        profile_revision__version=F("profile__revision_number"),
        matching_config__rubric_version=RUBRIC_VERSION,
    ).order_by("-created_at", "-pk").values("pk")[:1]
    candidates = VacancyAnalysis.objects.filter(
        status=VacancyAnalysis.Status.COMPLETED,
        profile_revision__version=F("profile__revision_number"),
        matching_config__rubric_version=RUBRIC_VERSION,
        score__lte=10,
    ).exclude(score_breakdown={}).annotate(latest_result_id=Subquery(latest_result))
    candidates = candidates.filter(pk=F("latest_result_id")).select_related(
        "profile", "profile_revision", "vacancy"
    ).order_by("profile_id", "vacancy_id")

    discarded = 0
    for candidate in candidates.iterator(chunk_size=200):
        with transaction.atomic():
            profile = Profile.objects.select_for_update().filter(
                pk=candidate.profile_id,
                owner__is_active=True,
                revision_number=candidate.profile_revision.version,
            ).first()
            if profile is None:
                continue

            analysis = VacancyAnalysis.objects.filter(
                pk=candidate.pk,
                profile=profile,
                profile_revision__version=profile.revision_number,
                status=VacancyAnalysis.Status.COMPLETED,
                matching_config__rubric_version=RUBRIC_VERSION,
                score__lte=10,
            ).filter(
                pk=Subquery(
                    VacancyAnalysis.objects.filter(
                        profile=OuterRef("profile"),
                        vacancy=OuterRef("vacancy"),
                        status=VacancyAnalysis.Status.COMPLETED,
                        profile_revision__version=F("profile__revision_number"),
                        matching_config__rubric_version=RUBRIC_VERSION,
                    ).order_by("-created_at", "-pk").values("pk")[:1]
                )
            ).exclude(score_breakdown={}).first()
            if analysis is None or not vacancy_location_is_eligible(analysis.vacancy, analysis.profile_revision):
                continue

            follow_up = VacancyFollowUp.objects.select_for_update().filter(
                profile=profile, vacancy=analysis.vacancy
            ).first()
            if follow_up and follow_up.status != VacancyFollowUp.Status.PENDING:
                continue

            pending_since = follow_up.state_changed_at if follow_up else analysis.completed_at
            if pending_since is None or pending_since > cutoff:
                continue

            _follow_up, changed = discard_follow_up(profile, analysis.vacancy, now=now)
            discarded += int(changed)

    logger.info("recommendations_auto_discarded count=%s cutoff=%s", discarded, cutoff.isoformat())
    return {"discarded": discarded, "cutoff": cutoff.isoformat()}


@shared_task(name="dashboard.tasks.archive_inactive_follow_ups")
def archive_inactive_follow_ups(retention_days=None):
    """Archive profile follow-ups whose current state has been unchanged for 30 days."""
    if retention_days is None:
        retention_days = current_follow_up_archive_days()
    else:
        try:
            retention_days = int(retention_days)
        except (TypeError, ValueError):
            retention_days = DEFAULT_FOLLOW_UP_ARCHIVE_DAYS
        if not 1 <= retention_days <= 365:
            retention_days = DEFAULT_FOLLOW_UP_ARCHIVE_DAYS
    now = timezone.now()
    # Ensure old implicit recommendations first enter Discarded and start its own retention period.
    discard_stale_recommendations.run()

    cutoff = now - timedelta(days=retention_days)
    due_ids = VacancyFollowUp.objects.filter(
        archived_at__isnull=True,
        state_changed_at__lte=cutoff,
    ).order_by("profile_id", "pk").values_list("pk", "profile_id")

    archived = 0
    for follow_up_id, profile_id in due_ids.iterator(chunk_size=200):
        with transaction.atomic():
            profile = Profile.objects.select_for_update().filter(pk=profile_id).first()
            if profile is None:
                continue
            follow_up = VacancyFollowUp.objects.select_for_update().filter(
                pk=follow_up_id,
                profile=profile,
                archived_at__isnull=True,
                state_changed_at__lte=cutoff,
            ).first()
            if follow_up is None:
                continue
            follow_up.archived_at = now
            follow_up.save(update_fields=["archived_at", "updated_at"])
            archived += 1

    logger.info("follow_ups_archived count=%s cutoff=%s", archived, cutoff.isoformat())
    return {"archived": archived, "cutoff": cutoff.isoformat()}
