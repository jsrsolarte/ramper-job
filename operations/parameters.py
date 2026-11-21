from django.conf import settings
from django.db import DatabaseError, transaction
from django.utils import timezone
from datetime import time

from .models import (AdminAuditEvent, AutomaticSearchSchedule, AutomaticSearchScheduleChange,
                     OperationalParameter, OperationalParameterChange)

REFRESH_INTERVAL_KEY = "source_refresh_minutes"
AUTO_DISCARD_DAYS_KEY = "auto_discard_days"
FOLLOW_UP_ARCHIVE_DAYS_KEY = "follow_up_archive_days"
PROCESSING_PAUSED_KEY = "processing_paused"
MIN_REFRESH_MINUTES = 15
MAX_REFRESH_MINUTES = 1440
MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 365
DEFAULT_AUTO_DISCARD_DAYS = 7
DEFAULT_FOLLOW_UP_ARCHIVE_DAYS = 30
DEFAULT_SEARCH_PAUSE_START = time(21, 0)
DEFAULT_SEARCH_PAUSE_END = time(7, 0)


def initial_refresh_interval_minutes():
    value = settings.JOB_REFRESH_MINUTES
    if MIN_REFRESH_MINUTES <= value <= MAX_REFRESH_MINUTES:
        return value
    return 120


def current_refresh_interval_minutes():
    value = current_parameter_value(REFRESH_INTERVAL_KEY, initial_refresh_interval_minutes())
    return value if value is not None else initial_refresh_interval_minutes()


def current_parameter_value(key, default):
    value = OperationalParameter.objects.filter(key=key).values_list("value", flat=True).first()
    return value if value is not None else default


def processing_is_paused():
    try:
        return bool(current_parameter_value(PROCESSING_PAUSED_KEY, 0))
    except DatabaseError:
        return False


def automatic_search_schedule():
    """Return persisted schedule, defaulting safely when no row exists."""
    try:
        row = AutomaticSearchSchedule.objects.filter(pk=1).first()
    except DatabaseError:
        row = None
    return {
        "enabled": row.enabled if row else True,
        "starts_at": row.starts_at if row else DEFAULT_SEARCH_PAUSE_START,
        "ends_at": row.ends_at if row else DEFAULT_SEARCH_PAUSE_END,
    }


@transaction.atomic
def save_automatic_search_schedule(*, actor, enabled, starts_at, ends_at):
    if starts_at == ends_at:
        raise ValueError("La hora de inicio y fin no pueden ser iguales.")
    current = automatic_search_schedule()
    row, _ = AutomaticSearchSchedule.objects.select_for_update().get_or_create(
        pk=1,
        defaults={"enabled": bool(enabled), "starts_at": starts_at, "ends_at": ends_at},
    )
    if (current["enabled"], current["starts_at"], current["ends_at"]) != (bool(enabled), starts_at, ends_at):
        AutomaticSearchScheduleChange.objects.create(
            actor=actor,
            previous_enabled=current["enabled"], previous_starts_at=current["starts_at"],
            previous_ends_at=current["ends_at"], new_enabled=bool(enabled),
            new_starts_at=starts_at, new_ends_at=ends_at,
        )
        row.enabled, row.starts_at, row.ends_at = bool(enabled), starts_at, ends_at
        row.updated_at = timezone.now()
        row.save(update_fields=("enabled", "starts_at", "ends_at", "updated_at"))
    return row


@transaction.atomic
def set_processing_paused(*, actor, paused):
    value = int(bool(paused))
    parameter, created = OperationalParameter.objects.select_for_update().get_or_create(
        key=PROCESSING_PAUSED_KEY,
        defaults={"value": value},
    )
    previous = False if created else bool(parameter.value)
    if previous == bool(value):
        return previous
    parameter.value = value
    parameter.updated_at = timezone.now()
    parameter.save(update_fields=("value", "updated_at"))
    AdminAuditEvent.objects.create(
        actor=actor,
        action=(AdminAuditEvent.Action.PROCESSING_PAUSED if value
                else AdminAuditEvent.Action.PROCESSING_RESUMED),
    )
    return previous


def default_parameter_value(key):
    return {
        REFRESH_INTERVAL_KEY: initial_refresh_interval_minutes(),
        AUTO_DISCARD_DAYS_KEY: DEFAULT_AUTO_DISCARD_DAYS,
        FOLLOW_UP_ARCHIVE_DAYS_KEY: DEFAULT_FOLLOW_UP_ARCHIVE_DAYS,
    }.get(key)


def current_retention_days(key, default):
    value = current_parameter_value(key, default)
    return value if MIN_RETENTION_DAYS <= value <= MAX_RETENTION_DAYS else default


def current_auto_discard_days():
    return current_retention_days(AUTO_DISCARD_DAYS_KEY, DEFAULT_AUTO_DISCARD_DAYS)


def current_follow_up_archive_days():
    return current_retention_days(FOLLOW_UP_ARCHIVE_DAYS_KEY, DEFAULT_FOLLOW_UP_ARCHIVE_DAYS)


@transaction.atomic
def save_parameter(*, actor, key, value):
    previous = current_parameter_value(key, default_parameter_value(key))
    parameter, _ = OperationalParameter.objects.select_for_update().get_or_create(
        key=key,
        defaults={"value": value},
    )
    if parameter.value != value:
        parameter.value = value
        parameter.updated_at = timezone.now()
        parameter.save(update_fields=("value", "updated_at"))
    if previous != value:
        OperationalParameterChange.objects.create(
            key=key,
            changed_by=actor,
            previous_value=previous,
            new_value=value,
        )
    return previous, value


@transaction.atomic
def save_refresh_interval(*, actor, value_minutes):
    return save_parameter(actor=actor, key=REFRESH_INTERVAL_KEY, value=value_minutes)


@transaction.atomic
def reset_refresh_interval(*, actor):
    previous = current_refresh_interval_minutes()
    OperationalParameter.objects.filter(key=REFRESH_INTERVAL_KEY).delete()
    new_value = initial_refresh_interval_minutes()
    if previous != new_value:
        OperationalParameterChange.objects.create(
            key=REFRESH_INTERVAL_KEY,
            changed_by=actor,
            previous_value=previous,
            new_value=new_value,
        )
    return previous, new_value
