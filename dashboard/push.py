import json
import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from dashboard.models import PushDailyAttempt, PushSubscription, RecommendationEvent, VacancyFollowUp
from dashboard.services import current_score_analyses
from profiles.locations import vacancy_location_is_eligible

logger = logging.getLogger(__name__)
BOGOTA = ZoneInfo("America/Bogota")
PUSH_TTL_SECONDS = 300
PUSH_WINDOW_MINUTES = 5
GENERIC_PUSH_TYPES = {"recommendations", "operational_alerts"}


def visible_recommendation_vacancy_ids(profile):
    analyses, revision, archived_ids = current_score_analyses(profile)
    if not revision:
        return set()
    follow_ups = {
        row.vacancy_id: row
        for row in VacancyFollowUp.objects.filter(
            profile=profile,
            vacancy_id__in=[analysis.vacancy_id for analysis in analyses],
            archived_at__isnull=True,
        )
    }
    return {
        analysis.vacancy_id
        for analysis in analyses
        if analysis.profile_revision.version == profile.revision_number
        and analysis.vacancy_id not in archived_ids
        and (
            follow_ups.get(analysis.vacancy_id) is None
            or follow_ups[analysis.vacancy_id].status == VacancyFollowUp.Status.PENDING
        )
        and vacancy_location_is_eligible(analysis.vacancy, revision)
    }


def _reserve_daily_attempt(subscription_id, now, local_date):
    with transaction.atomic():
        subscription = (
            PushSubscription.objects.select_for_update()
            .select_related("profile__owner")
            .filter(pk=subscription_id, active=True, profile__owner__is_active=True)
            .first()
        )
        if subscription is None:
            return None, None
        already_reserved = PushDailyAttempt.objects.filter(
            subscription_digest=subscription.endpoint_digest,
            local_date=local_date,
        ).exists()
        if already_reserved:
            return None, None

        visible_ids = visible_recommendation_vacancy_ids(subscription.profile)
        previous_daily_cutoff = now.astimezone(BOGOTA).replace(
            hour=9, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)
        if subscription.activated_at > previous_daily_cutoff:
            event_window_start = subscription.activated_at
        else:
            event_window_start = now.astimezone(BOGOTA).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        event_window_start = event_window_start.astimezone(timezone.get_current_timezone())
        latest_event_id = RecommendationEvent.objects.filter(
            profile=subscription.profile,
            created_at__lte=now,
        ).aggregate(max_id=Max("pk"))["max_id"] or subscription.last_event_cutoff_id
        eligible_events = RecommendationEvent.objects.filter(
            profile=subscription.profile,
            vacancy_id__in=visible_ids,
            created_at__gte=event_window_start,
            created_at__lte=now,
            pk__gt=max(subscription.last_event_cutoff_id, subscription.profile.recommendations_reviewed_through),
        ) if visible_ids else RecommendationEvent.objects.none()
        has_new_events = eligible_events.exists()
        # Advance on every daily cut, even if the events are reviewed or no longer visible.
        subscription.last_event_cutoff_id = max(subscription.last_event_cutoff_id, latest_event_id)
        subscription.save(update_fields=["last_event_cutoff_id", "updated_at"])
        if not has_new_events:
            return None, None

        attempt = PushDailyAttempt.objects.create(
            subscription=subscription,
            subscription_digest=subscription.endpoint_digest,
            local_date=local_date,
            status=PushDailyAttempt.Status.RESERVED,
        )
        return attempt.pk, {
            "endpoint": subscription.endpoint,
            "keys": {"p256dh": subscription.p256dh_key, "auth": subscription.auth_key},
        }


def _send_generic_push(subscription_info, notification_type="recommendations"):
    from pywebpush import webpush

    if notification_type not in GENERIC_PUSH_TYPES:
        raise ValueError("unsupported_push_type")
    if not (
        settings.PUSH_VAPID_PUBLIC_KEY
        and settings.PUSH_VAPID_PRIVATE_KEY
        and settings.PUSH_VAPID_SUBJECT
    ):
        raise RuntimeError("push_not_configured")
    return webpush(
        subscription_info=subscription_info,
        data=json.dumps({"type": notification_type}),
        vapid_private_key=settings.PUSH_VAPID_PRIVATE_KEY,
        vapid_claims={"sub": settings.PUSH_VAPID_SUBJECT},
        ttl=PUSH_TTL_SECONDS,
        timeout=8,
    )


def send_daily_recommendation_summaries(now=None, sender=None):
    """Reserve and attempt at most one generic push per active device and local day."""
    now = now or timezone.now()
    local_now = now.astimezone(BOGOTA)
    if local_now.hour != 9 or local_now.minute > PUSH_WINDOW_MINUTES:
        return {"skipped_outside_window": True, "attempted": 0}
    local_date = local_now.date()
    send = sender or _send_generic_push
    attempted = 0

    for subscription_id in PushSubscription.objects.filter(
        active=True,
        profile__owner__is_active=True,
    ).order_by("pk").values_list("pk", flat=True):
        attempt_id, subscription_info = _reserve_daily_attempt(subscription_id, now, local_date)
        if not attempt_id:
            continue
        attempted += 1
        try:
            send(subscription_info)
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            response = getattr(exc, "response", None)
            if status_code is None and response is not None:
                status_code = getattr(response, "status_code", None)
            if status_code in {404, 410}:
                PushSubscription.objects.filter(pk=subscription_id).delete()
                failure_category = "expired"
            elif isinstance(exc, RuntimeError) and str(exc) == "push_not_configured":
                failure_category = "not_configured"
            else:
                failure_category = "push_error"
            PushDailyAttempt.objects.filter(pk=attempt_id).update(
                status=PushDailyAttempt.Status.FAILED,
                failure_category=failure_category,
                finished_at=timezone.now(),
            )
            # Do not log the exception; push errors may contain a private endpoint or response body.
            logger.warning("Daily push attempt failed (category=%s)", failure_category)
        else:
            PushDailyAttempt.objects.filter(pk=attempt_id).update(
                status=PushDailyAttempt.Status.SENT,
                finished_at=timezone.now(),
            )
    return {"skipped_outside_window": False, "attempted": attempted}
