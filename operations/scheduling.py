from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import DatabaseError, transaction
from django.utils import timezone

from .models import PeriodicRefreshState
from .parameters import (PROCESSING_PAUSED_KEY, automatic_search_schedule, current_parameter_value,
                         current_refresh_interval_minutes)

SCHEDULE_TIME_ZONE = ZoneInfo("America/Bogota")


def automatic_searches_paused(*, now=None):
    """Whether automatic source queries are inside the configured local quiet window."""
    config = automatic_search_schedule()
    if not config["enabled"]:
        return False
    local_now = timezone.localtime(now or timezone.now(), SCHEDULE_TIME_ZONE)
    current = local_now.timetz().replace(tzinfo=None)
    start, end = config["starts_at"], config["ends_at"]
    if start < end:
        return start <= current < end
    return current >= start or current < end


def next_automatic_search_time(*, now=None):
    config = automatic_search_schedule()
    if not config["enabled"]:
        return None
    instant = now or timezone.now()
    local_now = timezone.localtime(instant, SCHEDULE_TIME_ZONE)
    current = local_now.timetz().replace(tzinfo=None)
    start, end = config["starts_at"], config["ends_at"]
    inside = (start <= current < end) if start < end else (current >= start or current < end)
    if not inside:
        return instant
    end_date = local_now.date()
    if start > end and current >= start:
        end_date += timedelta(days=1)
    return timezone.make_aware(datetime.combine(end_date, end), SCHEDULE_TIME_ZONE)


def record_periodic_refresh_start(*, started_at=None):
    """Persist the start time for the global Celery Beat source-refresh cycle."""
    timestamp = started_at or timezone.now()
    PeriodicRefreshState.objects.update_or_create(pk=1, defaults={"last_started_at": timestamp})
    return timestamp


@transaction.atomic
def claim_periodic_refresh_start(*, started_at=None):
    """Atomically claim at most one due global automatic cycle per interval."""
    timestamp = started_at or timezone.now()
    state, created = PeriodicRefreshState.objects.get_or_create(pk=1, defaults={"last_started_at": timestamp})
    state = PeriodicRefreshState.objects.select_for_update().get(pk=1)
    if not created and state.last_started_at + timedelta(
        minutes=current_refresh_interval_minutes(),
    ) > timestamp:
        return None
    state.last_started_at = timestamp
    state.save(update_fields=("last_started_at",))
    return timestamp


def next_periodic_refresh_schedule(*, now=None):
    """Return the shared estimate or an explicit paused/unavailable state."""
    try:
        paused = bool(current_parameter_value(PROCESSING_PAUSED_KEY, 0))
        if paused:
            return {"status": "paused", "next_at": None}

        current = now or timezone.now()
        quiet = automatic_searches_paused(now=current)
        state = PeriodicRefreshState.objects.filter(pk=1).first()
        interval = timedelta(minutes=current_refresh_interval_minutes())
        # Before the first persisted cycle, provide a useful estimate from now.
        next_at = (state.last_started_at if state else current) + interval
        if quiet:
            # A cycle that became overdue before or during the quiet window is
            # estimated at the first allowed instant, never in the past.
            quiet_end = next_automatic_search_time(now=current)
            if quiet_end and next_at < quiet_end:
                next_at = quiet_end
        elif automatic_searches_paused(now=next_at):
            next_allowed = next_automatic_search_time(now=next_at)
            if next_allowed and next_allowed > next_at:
                next_at = next_allowed
    except DatabaseError:
        return {"status": "unavailable", "next_at": None}

    return {
        "status": "scheduled",
        "next_at": timezone.localtime(next_at) if timezone.is_aware(next_at) else next_at,
        "is_overdue": next_at <= (now or timezone.now()),
        "quiet_window": quiet,
        "quiet_window_end": next_automatic_search_time(now=current) if quiet else None,
    }
