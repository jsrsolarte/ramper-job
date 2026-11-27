"""Durable, privacy-safe detection and notification of operational incidents."""

import hashlib
import json
import logging
from collections import defaultdict
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, Max, OuterRef, Q
from django.utils import timezone

from dashboard.models import PushSubscription
from matching.models import VacancyAnalysis
from operations.models import (
    OperationalAlertPushAttempt,
    OperationalAlertState,
    OperationalAlertSubscription,
    OperationalIncident,
    OperationalRun,
    RefreshBatch,
    RefreshWorkItem,
    RefreshWorkProfile,
)
from operations.parameters import processing_is_paused
from operations.scheduling import automatic_searches_paused, next_periodic_refresh_schedule
from operations.services import SAFE_ERROR_SUMMARIES
from profiles.models import Profile

logger = logging.getLogger(__name__)

EVALUATION_INTERVAL = timedelta(minutes=5)
INCIDENT_WINDOW = timedelta(minutes=30)
INCIDENT_THRESHOLD = 3
RECOVERY_CHECKS = 2
HEALTH_MAX_AGE = timedelta(minutes=15)
PUSH_COOLDOWN = timedelta(hours=6)
PUSH_TTL_SECONDS = 300
SAFE_SOURCES = {"elempleo_co", "computrabajo_co", "magneto_co"}
ACTIVE_INCIDENT_STATUSES = (OperationalIncident.Status.OPEN, OperationalIncident.Status.ACKNOWLEDGED)


def _safe_component(kind, source=""):
    if kind == OperationalRun.Kind.INGESTION:
        return source if source in SAFE_SOURCES else "otra_fuente"
    if kind == OperationalRun.Kind.RECOVERY:
        return "recuperacion"
    return "analisis"


def _safe_error_category(value):
    if value in SAFE_ERROR_SUMMARIES:
        return value
    if value.startswith("omniroute.http_") and value.rsplit("_", 1)[-1].isdigit():
        return "omniroute.http_error"
    return "otro_error"


def _eligible_profiles():
    return Profile.objects.filter(
        owner__is_active=True,
        search_enabled=True,
        cv_file__gt="",
        revision_number__gt=0,
    )


def _failure_findings(*, now, activated_at):
    grouped = defaultdict(list)
    cutoff = max(activated_at, now - INCIDENT_WINDOW)
    runs = OperationalRun.objects.filter(
        status__in=(OperationalRun.Status.RETRYING, OperationalRun.Status.FAILED),
        started_at__lte=now,
    ).filter(Q(started_at__gte=cutoff) | Q(finished_at__gte=cutoff)).exclude(error_category="").only(
        "pk", "kind", "source", "error_category", "started_at", "finished_at",
    )
    for run in runs.iterator():
        occurred_at = run.finished_at or run.started_at
        if occurred_at < cutoff:
            continue
        component = _safe_component(run.kind, run.source)
        category = _safe_error_category(run.error_category)
        grouped[(OperationalIncident.Kind.RECURRING_FAILURE, component, category)].append(run)

    findings = {}
    for key, events in grouped.items():
        if len(events) < INCIDENT_THRESHOLD:
            continue
        findings[key] = {
            "first_observed_at": min(event.finished_at or event.started_at for event in events),
            "last_observed_at": max(event.finished_at or event.started_at for event in events),
            "count": len(events),
        }
    return findings


def _no_progress_findings(*, now, activated_at, globally_paused, quiet_window):
    if globally_paused:
        return {}

    stale_before = now - INCIDENT_WINDOW
    grouped = defaultdict(list)
    eligible_links = RefreshWorkProfile.objects.filter(
        work_item_id=OuterRef("pk"),
        batch_profile__profile__owner__is_active=True,
        batch_profile__profile__search_enabled=True,
    )
    work = RefreshWorkItem.objects.annotate(has_eligible_profile=Exists(eligible_links)).filter(
        has_eligible_profile=True,
        status__in=(RefreshWorkItem.Status.QUEUED, RefreshWorkItem.Status.RUNNING),
    ).select_related("batch").only(
        "pk", "source", "phase", "status", "heartbeat_at", "last_dispatched_at", "created_at",
        "lease_expires_at", "batch__origin",
    )
    if quiet_window:
        work = work.exclude(batch__origin=RefreshBatch.Origin.AUTOMATIC)
    for item in work.iterator():
        progress_at = item.heartbeat_at if item.status == RefreshWorkItem.Status.RUNNING else (
            item.last_dispatched_at or item.created_at
        )
        if item.status == RefreshWorkItem.Status.RUNNING and item.lease_expires_at and item.lease_expires_at > now:
            progress_at = max(progress_at, item.lease_expires_at)
        progress_at = max(progress_at, activated_at)
        if progress_at > stale_before:
            continue
        source = item.source if item.source in SAFE_SOURCES else "otra_fuente"
        grouped[source].append(progress_at)

    for analysis in VacancyAnalysis.objects.filter(
        status=VacancyAnalysis.Status.PENDING,
        profile__owner__is_active=True,
    ).only("pk", "created_at", "last_enqueued_at", "processing_started_at").iterator():
        progress_at = analysis.processing_started_at or analysis.last_enqueued_at or analysis.created_at
        progress_at = max(progress_at, activated_at)
        if progress_at <= stale_before:
            grouped["analisis"].append(progress_at)

    findings = {}
    for component, timestamps in grouped.items():
        findings[(OperationalIncident.Kind.NO_PROGRESS, component, "sin_progreso")] = {
            "first_observed_at": min(timestamps),
            "last_observed_at": max(timestamps),
            "count": len(timestamps),
        }
    return findings


def _periodic_cycle_findings(*, now, activated_at, profiles_available, globally_paused):
    if globally_paused or not profiles_available:
        return {}
    schedule = next_periodic_refresh_schedule(now=now)
    if schedule["status"] != "overdue" or not schedule.get("next_at"):
        return {}
    overdue_since = max(schedule["next_at"], activated_at)
    if now - overdue_since < INCIDENT_WINDOW:
        return {}
    key = (OperationalIncident.Kind.PERIODIC_OVERDUE, "planificador", "ciclo_no_iniciado")
    return {key: {
        "first_observed_at": overdue_since,
        "last_observed_at": now,
        "count": 1,
    }}


def _reconcile_incidents(findings, *, now):
    active = list(OperationalIncident.objects.select_for_update().filter(
        status__in=ACTIVE_INCIDENT_STATUSES,
    ))
    active_by_key = {(row.kind, row.component, row.category): row for row in active}
    for key, evidence in findings.items():
        row = active_by_key.get(key)
        if row is None:
            OperationalIncident.objects.create(
                kind=key[0], component=key[1], category=key[2],
                first_observed_at=evidence["first_observed_at"],
                last_observed_at=evidence["last_observed_at"],
                count=evidence["count"],
            )
            continue
        row.last_observed_at = evidence["last_observed_at"]
        row.count = evidence["count"]
        row.consecutive_clear_checks = 0
        row.save(update_fields=("last_observed_at", "count", "consecutive_clear_checks", "updated_at"))

    for key, row in active_by_key.items():
        if key in findings:
            continue
        row.consecutive_clear_checks += 1
        fields = ["consecutive_clear_checks", "updated_at"]
        if row.consecutive_clear_checks >= RECOVERY_CHECKS:
            row.status = OperationalIncident.Status.RECOVERED
            row.recovered_at = now
            fields.extend(("status", "recovered_at"))
        row.save(update_fields=fields)


def evaluate_operational_alerts(*, now=None, sender=None):
    """Evaluate durable signals once; unknown data never resolves incidents."""
    now = now or timezone.now()
    try:
        OperationalAlertState.objects.get_or_create(pk=1, defaults={"activated_at": now})
        with transaction.atomic():
            state = OperationalAlertState.objects.select_for_update().get(pk=1)
            if state.last_started_at and now - state.last_started_at < EVALUATION_INTERVAL - timedelta(minutes=1):
                return {"status": "duplicate", "incidents": 0, "push_attempts": 0}
            state.last_started_at = now
            state.last_error_category = ""
            state.save(update_fields=("last_started_at", "last_error_category"))
            globally_paused = processing_is_paused()
            quiet_window = automatic_searches_paused(now=now)
            profiles_available = _eligible_profiles().exists()
            findings = _failure_findings(now=now, activated_at=state.activated_at)
            findings.update(_no_progress_findings(
                now=now,
                activated_at=state.activated_at,
                globally_paused=globally_paused,
                quiet_window=quiet_window,
            ))
            findings.update(_periodic_cycle_findings(
                now=now,
                activated_at=state.activated_at,
                profiles_available=profiles_available,
                globally_paused=globally_paused,
            ))
            _reconcile_incidents(findings, now=now)
            state.last_succeeded_at = now
            state.last_error_category = ""
            state.save(update_fields=("last_succeeded_at", "last_error_category"))
    except Exception:
        try:
            OperationalAlertState.objects.filter(pk=1).update(
                last_started_at=now,
                last_error_category="evaluation_error",
            )
        except Exception:
            pass
        logger.warning("operational_alert_evaluation_failed category=evaluation_error")
        return {"status": "unknown", "incidents": 0, "push_attempts": 0}

    push_result = send_pending_operational_alerts(now=now, sender=sender)
    return {"status": "ok", "incidents": len(findings), "push_attempts": push_result["attempted"]}


def operational_alert_health(*, now=None):
    now = now or timezone.now()
    state = OperationalAlertState.objects.filter(pk=1).first()
    if state is None or state.last_succeeded_at is None:
        return {"status": "unknown", "last_succeeded_at": state.last_succeeded_at if state else None}
    if now - state.last_succeeded_at > HEALTH_MAX_AGE:
        return {"status": "unknown", "last_succeeded_at": state.last_succeeded_at}
    if state.last_started_at and state.last_started_at > state.last_succeeded_at:
        return {"status": "unknown", "last_succeeded_at": state.last_succeeded_at}
    return {"status": "verified", "last_succeeded_at": state.last_succeeded_at}


def _reserve_operational_push(subscription_id, *, now):
    with transaction.atomic():
        subscription = OperationalAlertSubscription.objects.select_for_update().filter(
            pk=subscription_id,
            active=True,
            user__is_active=True,
            user__is_superuser=True,
        ).first()
        if subscription is None:
            return None
        if OperationalAlertPushAttempt.objects.filter(
            subscription_digest=subscription.endpoint_digest,
            reserved_at__gte=now - PUSH_COOLDOWN,
        ).exists():
            return None

        new_active = OperationalIncident.objects.filter(
            pk__gt=subscription.last_notified_incident_id,
            status__in=ACTIVE_INCIDENT_STATUSES,
        )
        latest_new_id = new_active.aggregate(value=Max("pk"))["value"]
        if latest_new_id is None:
            latest_any_id = OperationalIncident.objects.aggregate(value=Max("pk"))["value"] or 0
            if latest_any_id > subscription.last_notified_incident_id:
                subscription.last_notified_incident_id = latest_any_id
                subscription.save(update_fields=("last_notified_incident_id", "updated_at"))
            return None

        attempt = OperationalAlertPushAttempt.objects.create(
            subscription=subscription,
            subscription_digest=subscription.endpoint_digest,
            latest_incident_id=latest_new_id,
        )
        previous_cutoff = subscription.last_notified_incident_id
        subscription.last_notified_incident_id = latest_new_id
        subscription.save(update_fields=("last_notified_incident_id", "updated_at"))
        return {
            "attempt_id": attempt.pk,
            "subscription_id": subscription.pk,
            "previous_cutoff": previous_cutoff,
            "latest_incident_id": latest_new_id,
            "subscription_info": {
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh_key, "auth": subscription.auth_key},
            },
        }


def send_pending_operational_alerts(*, now=None, sender=None):
    now = now or timezone.now()
    attempted = 0
    send = sender or _send_operational_push
    subscription_ids = OperationalAlertSubscription.objects.filter(
        active=True,
        user__is_active=True,
        user__is_superuser=True,
    ).order_by("pk").values_list("pk", flat=True)
    for subscription_id in subscription_ids:
        reservation = _reserve_operational_push(subscription_id, now=now)
        if reservation is None:
            continue
        attempted += 1
        still_active = OperationalIncident.objects.filter(
            pk__gt=reservation["previous_cutoff"],
            pk__lte=reservation["latest_incident_id"],
            status__in=ACTIVE_INCIDENT_STATUSES,
        ).exists()
        if not still_active:
            OperationalAlertPushAttempt.objects.filter(pk=reservation["attempt_id"]).update(
                status=OperationalAlertPushAttempt.Status.FAILED,
                failure_category="no_active_incident",
                finished_at=timezone.now(),
            )
            continue
        try:
            send(reservation["subscription_info"])
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            response = getattr(exc, "response", None)
            if status_code is None and response is not None:
                status_code = getattr(response, "status_code", None)
            if status_code in {404, 410}:
                OperationalAlertSubscription.objects.filter(pk=subscription_id).update(active=False)
                failure_category = "expired"
            else:
                failure_category = "push_error"
            OperationalAlertPushAttempt.objects.filter(pk=reservation["attempt_id"]).update(
                status=OperationalAlertPushAttempt.Status.FAILED,
                failure_category=failure_category,
                finished_at=timezone.now(),
            )
            logger.warning("operational_alert_push_failed category=%s", failure_category)
        else:
            OperationalAlertPushAttempt.objects.filter(pk=reservation["attempt_id"]).update(
                status=OperationalAlertPushAttempt.Status.SENT,
                finished_at=timezone.now(),
            )
    return {"attempted": attempted}


def _send_operational_push(subscription_info):
    from dashboard.push import _send_generic_push

    return _send_generic_push(subscription_info, notification_type="operational_alerts")


def valid_push_endpoint(endpoint):
    endpoint = str(endpoint or "").strip()
    parsed = urlparse(endpoint)
    if len(endpoint) > 4096 or parsed.scheme != "https" or not parsed.netloc:
        return ""
    return endpoint


def push_endpoint_digest(endpoint):
    return hashlib.sha256(endpoint.encode("utf-8")).hexdigest()


def parse_push_request(body):
    if len(body) > 8192:
        return None
    try:
        payload = json.loads(body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None
