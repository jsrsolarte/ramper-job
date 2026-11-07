from datetime import date, datetime

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime


def relative_age(value: datetime | None, *, now: datetime | None = None) -> str:
    """Return a compact Spanish age label, or an empty string when unknown."""
    if value is None:
        return ""
    now = now or timezone.now()
    if timezone.is_aware(value) and timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())
    elif timezone.is_naive(value) and timezone.is_aware(now):
        value = timezone.make_aware(value, timezone.get_current_timezone())

    seconds = max(0, int((now - value).total_seconds()))
    if seconds < 60:
        return "hace menos de un minuto"
    if seconds < 3600:
        minutes = seconds // 60
        return f"hace {minutes} min"
    if seconds < 86400:
        hours = seconds // 3600
        return f"hace {hours} hora" if hours == 1 else f"hace {hours} horas"
    days = seconds // 86400
    return f"hace {days} día" if days == 1 else f"hace {days} días"


def publication_age(value: datetime | None, raw_data: dict | None, *, now: datetime | None = None) -> tuple[str, str]:
    """Return age and accessible date, respecting sources that provide only a date."""
    raw_data = raw_data or {}
    details = raw_data.get("details") or {}
    raw_timestamp = parse_datetime(str(raw_data.get("datePosted", "")))
    date_only = parse_date(str(details.get("date_posted", "")))
    if date_only is None and raw_timestamp is None:
        date_only = parse_date(str(raw_data.get("datePosted", "")))
    if date_only and not raw_timestamp:
        now = now or timezone.now()
        local_now = timezone.localtime(now) if timezone.is_aware(now) else now
        delta_days = max(0, (local_now.date() - date_only).days)
        if delta_days == 0:
            age = "hoy"
        elif delta_days == 1:
            age = "ayer"
        else:
            age = f"hace {delta_days} días"
        return age, date_only.strftime("%d/%m/%Y")
    if value is None:
        return "", ""
    return relative_age(value, now=now), timezone.localtime(value).strftime("%d/%m/%Y %H:%M")
