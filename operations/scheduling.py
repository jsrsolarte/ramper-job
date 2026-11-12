from datetime import timedelta

from django.db import DatabaseError
from django.utils import timezone

from .models import PeriodicRefreshState
from .parameters import PROCESSING_PAUSED_KEY, current_parameter_value, current_refresh_interval_minutes


def record_periodic_refresh_start(*, started_at=None):
    """Persist the start time for the global Celery Beat source-refresh cycle."""
    timestamp = started_at or timezone.now()
    PeriodicRefreshState.objects.update_or_create(pk=1, defaults={"last_started_at": timestamp})
    return timestamp


def next_periodic_refresh_schedule(*, now=None):
    """Return the shared estimate or an explicit paused/unavailable state."""
    try:
        paused = bool(current_parameter_value(PROCESSING_PAUSED_KEY, 0))
        if paused:
            return {"status": "paused", "next_at": None}

        state = PeriodicRefreshState.objects.filter(pk=1).first()
        if state is None:
            return {"status": "unavailable", "next_at": None}

        next_at = state.last_started_at + timedelta(minutes=current_refresh_interval_minutes())
    except DatabaseError:
        return {"status": "unavailable", "next_at": None}

    return {
        "status": "scheduled",
        "next_at": timezone.localtime(next_at) if timezone.is_aware(next_at) else next_at,
        "is_overdue": next_at <= (now or timezone.now()),
    }
