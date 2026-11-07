from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import OperationalParameter, OperationalParameterChange

REFRESH_INTERVAL_KEY = "source_refresh_minutes"
AUTO_DISCARD_DAYS_KEY = "auto_discard_days"
FOLLOW_UP_ARCHIVE_DAYS_KEY = "follow_up_archive_days"
MIN_REFRESH_MINUTES = 15
MAX_REFRESH_MINUTES = 1440
MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 365
DEFAULT_AUTO_DISCARD_DAYS = 7
DEFAULT_FOLLOW_UP_ARCHIVE_DAYS = 30


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
