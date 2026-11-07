from django.db import transaction
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from matching.models import ProfileVacancyDiscovery


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
