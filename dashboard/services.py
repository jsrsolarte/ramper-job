from django.db import transaction
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone

from dashboard.models import VacancyFollowUp
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
        profile_revision__version=F("profile__revision_number"),
    ).order_by("-created_at", "-pk").values("pk")[:1]
    analyses = list(
        VacancyAnalysis.objects.filter(
            profile=profile,
            status=VacancyAnalysis.Status.COMPLETED,
            profile_revision__version=profile.revision_number,
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
    if revision:
        analyses = [
            analysis for analysis in analyses
            if analysis.vacancy_id not in archived_vacancy_ids
            and vacancy_location_is_eligible(analysis.vacancy, revision)
        ]
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
