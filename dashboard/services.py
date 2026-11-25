from django.db import transaction
from django.db.models import F, Max, OuterRef, Subquery
from django.utils import timezone

from dashboard.models import RecommendationEvent, VacancyFollowUp
from matching.models import ProfileVacancyDiscovery, VacancyAnalysis
from profiles.locations import vacancy_location_is_eligible


def current_score_analyses(profile):
    """Return the scored analyses currently visible on the applicant dashboard."""
    if not profile:
        return [], None, set()

    revision = profile.revisions.filter(version=profile.revision_number).first()
    latest_result = VacancyAnalysis.objects.filter(
        profile=OuterRef("profile"),
        vacancy=OuterRef("vacancy"),
        status=VacancyAnalysis.Status.COMPLETED,
    ).order_by("-completed_at", "-created_at", "-pk").values("pk")[:1]
    analyses = list(
        VacancyAnalysis.objects.filter(
            profile=profile,
            status=VacancyAnalysis.Status.COMPLETED,
            score_stars__isnull=False,
        )
        .exclude(score_breakdown={})
        .annotate(latest_result_id=Subquery(latest_result))
        .filter(pk=F("latest_result_id"))
        .select_related("vacancy", "organization")
        .order_by("-score_stars", "-created_at")
    )
    archived_vacancy_ids = set(
        VacancyFollowUp.objects.filter(profile=profile, archived_at__isnull=False)
        .values_list("vacancy_id", flat=True)
    )
    analyses = [analysis for analysis in analyses if analysis.vacancy_id not in archived_vacancy_ids]
    return analyses, revision, archived_vacancy_ids


def dashboard_follow_up_summary(profile, analyses):
    """Return current follow-up rows and counts, including implicit pending."""
    counts = {status: 0 for status, _label in VacancyFollowUp.Status.choices}
    if not profile or not analyses:
        return counts, {}

    vacancy_ids = [analysis.vacancy_id for analysis in analyses]
    follow_ups = {
        follow_up.vacancy_id: follow_up
        for follow_up in VacancyFollowUp.objects.filter(
            profile=profile,
            vacancy_id__in=vacancy_ids,
            archived_at__isnull=True,
        )
    }
    for vacancy_id in vacancy_ids:
        follow_up = follow_ups.get(vacancy_id)
        status = follow_up.status if follow_up else VacancyFollowUp.Status.PENDING
        if status in counts:
            counts[status] += 1
    return counts, follow_ups


def dashboard_follow_up_counts(profile, analyses):
    """Count current dashboard vacancies by follow-up state."""
    counts, _follow_ups = dashboard_follow_up_summary(profile, analyses)
    return counts


@transaction.atomic
def register_recommendation_event(profile, vacancy, *, source_analysis=None, now=None):
    """Record the first visible recommendation after the profile's baseline."""
    now = now or timezone.now()
    profile = type(profile).objects.select_for_update().select_related("owner").get(pk=profile.pk)
    if not profile.owner.is_active:
        return None, False

    visible_analyses, _revision, archived_ids = current_score_analyses(profile)
    analysis = next(
        (item for item in visible_analyses if item.vacancy_id == vacancy.pk),
        None,
    )
    if (
        analysis is None
        or analysis.profile_revision.version != profile.revision_number
        or (source_analysis is not None and analysis.pk != source_analysis.pk)
        or not vacancy_location_is_eligible(vacancy, analysis.profile_revision)
        or vacancy.pk in archived_ids
    ):
        return None, False

    follow_up = VacancyFollowUp.objects.filter(profile=profile, vacancy=vacancy).first()
    if follow_up and follow_up.status != VacancyFollowUp.Status.PENDING:
        return None, False

    event = RecommendationEvent.objects.filter(profile=profile, vacancy=vacancy).first()
    if event:
        return event, False

    # Do not turn recommendations already visible when tracking began into new events.
    # A later explicit restoration is a new visible transition and may create the first event.
    previously_visible = VacancyAnalysis.objects.filter(
        profile=profile,
        vacancy=vacancy,
        status=VacancyAnalysis.Status.COMPLETED,
        profile_revision__version=profile.revision_number,
        completed_at__lt=profile.recommendation_tracking_started_at,
        score_stars__isnull=False,
    ).exclude(score_breakdown={}).exists()
    if previously_visible and not (
        follow_up
        and follow_up.status == VacancyFollowUp.Status.PENDING
        and follow_up.state_changed_at >= profile.recommendation_tracking_started_at
    ):
        return None, False

    event, created = RecommendationEvent.objects.get_or_create(
        profile=profile,
        vacancy=vacancy,
        defaults={"created_at": now},
    )
    return event, created


def new_recommendation_summary(profile):
    """Return the unread count and a safe visible-event cutoff for a profile."""
    if not profile or not profile.owner.is_active:
        return {"count": 0, "cutoff": profile.recommendations_reviewed_through if profile else 0}

    analyses, revision, archived_ids = current_score_analyses(profile)
    if not revision:
        return {"count": 0, "cutoff": profile.recommendations_reviewed_through}

    _counts, follow_ups = dashboard_follow_up_summary(profile, analyses)
    visible_vacancy_ids = {
        analysis.vacancy_id
        for analysis in analyses
        if analysis.profile_revision.version == profile.revision_number
        and analysis.vacancy_id not in archived_ids
        and (follow_ups.get(analysis.vacancy_id) is None
             or follow_ups[analysis.vacancy_id].status == VacancyFollowUp.Status.PENDING)
        and vacancy_location_is_eligible(analysis.vacancy, revision)
    }
    if not visible_vacancy_ids:
        return {"count": 0, "cutoff": profile.recommendations_reviewed_through}

    unread_events = RecommendationEvent.objects.filter(
        profile=profile,
        vacancy_id__in=visible_vacancy_ids,
        created_at__gte=profile.recommendation_tracking_started_at,
        pk__gt=profile.recommendations_reviewed_through,
    )
    return {
        "count": unread_events.count(),
        "cutoff": unread_events.aggregate(cutoff=Max("pk"))["cutoff"]
        or profile.recommendations_reviewed_through,
    }


@transaction.atomic
def mark_recommendations_reviewed(profile, requested_cutoff):
    """Advance only to the rendered cutoff, bounded by currently visible events."""
    profile = type(profile).objects.select_for_update().select_related("owner").get(pk=profile.pk)
    if not profile.owner.is_active:
        return profile.recommendations_reviewed_through

    try:
        requested_cutoff = max(0, int(requested_cutoff))
    except (TypeError, ValueError):
        return profile.recommendations_reviewed_through

    summary = new_recommendation_summary(profile)
    safe_cutoff = min(requested_cutoff, summary["cutoff"])
    if safe_cutoff > profile.recommendations_reviewed_through:
        profile.recommendations_reviewed_through = safe_cutoff
        profile.save(update_fields=["recommendations_reviewed_through"])
    return profile.recommendations_reviewed_through


@transaction.atomic
def discard_follow_up(profile, vacancy, *, now=None):
    """Move a profile's follow-up to discarded and preserve its previous stage."""
    now = now or timezone.now()
    follow_up = (
        VacancyFollowUp.objects.select_for_update()
        .filter(profile=profile, vacancy=vacancy)
        .first()
    )
    if follow_up is None:
        follow_up = VacancyFollowUp.objects.create(
            profile=profile,
            vacancy=vacancy,
            status=VacancyFollowUp.Status.DISCARDED,
            previous_status=VacancyFollowUp.Status.PENDING,
            state_changed_at=now,
        )
        return follow_up, True

    if follow_up.status == VacancyFollowUp.Status.DISCARDED:
        return follow_up, False

    follow_up.previous_status = follow_up.status
    follow_up.status = VacancyFollowUp.Status.DISCARDED
    follow_up.state_changed_at = now
    follow_up.save(update_fields=["previous_status", "status", "state_changed_at", "updated_at"])
    return follow_up, True


@transaction.atomic
def apply_discovery_score_threshold(profile, vacancy, score, *, now=None):
    """Evaluate the first completed score against the threshold captured at discovery."""
    now = now or timezone.now()
    discovery, _ = ProfileVacancyDiscovery.objects.select_for_update().get_or_create(
        profile=profile,
        vacancy=vacancy,
        defaults={"auto_discard_threshold": profile.min_score or 0},
    )
    if discovery.auto_discard_evaluated_at:
        return False

    discarded = False
    if discovery.auto_discard_threshold > 0 and score < discovery.auto_discard_threshold:
        follow_up = (
            VacancyFollowUp.objects.select_for_update()
            .filter(profile=profile, vacancy=vacancy)
            .first()
        )
        if follow_up is None:
            VacancyFollowUp.objects.create(
                profile=profile,
                vacancy=vacancy,
                status=VacancyFollowUp.Status.DISCARDED,
                previous_status=VacancyFollowUp.Status.PENDING,
                state_changed_at=now,
            )
            discarded = True
        elif (
            follow_up.status == VacancyFollowUp.Status.PENDING
            and follow_up.archived_at is None
        ):
            follow_up.previous_status = VacancyFollowUp.Status.PENDING
            follow_up.status = VacancyFollowUp.Status.DISCARDED
            follow_up.state_changed_at = now
            follow_up.save(update_fields=["previous_status", "status", "state_changed_at", "updated_at"])
            discarded = True

    discovery.auto_discard_evaluated_at = now
    discovery.save(update_fields=["auto_discard_evaluated_at"])
    return discarded
