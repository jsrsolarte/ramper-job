import logging
import uuid
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import AdminCommandRun, OperationalRun, RefreshLease

logger = logging.getLogger(__name__)


SAFE_ERROR_SUMMARIES = {
    "source_unavailable": "La fuente de empleo no respondió.",
    "source_error": "No fue posible completar la consulta a la fuente.",
    "omniroute.timeout": "Se agotó el tiempo de espera de OmniRoute.",
    "omniroute.connection": "No fue posible conectar con OmniRoute.",
    "omniroute.http_error": "OmniRoute rechazó la solicitud.",
    "omniroute.model_unsupported": "La combinación de OmniRoute seleccionó modelos no compatibles.",
    "omniroute.request": "No fue posible completar la solicitud a OmniRoute.",
    "omniroute.error": "No fue posible obtener una respuesta utilizable de OmniRoute.",
    "omniroute.invalid_json": "OmniRoute respondió con contenido que no es JSON válido.",
    "omniroute.invalid_shape": "OmniRoute devolvió una respuesta incompleta.",
    "analysis_invalid": "La respuesta de IA no cumple el formato esperado.",
    "analysis_error": "Ocurrió un error interno durante el análisis.",
    "execution_interrupted": "La ejecución no finalizó y el proceso trabajador se detuvo.",
    "analysis.recovery_exhausted": "El análisis agotó sus recuperaciones automáticas.",
    "analysis.expired": "Venció el plazo configurado para analizar la vacante.",
}


def begin_run(*, kind, operation, source="", task_id=""):
    return OperationalRun.objects.create(
        kind=kind,
        operation=operation,
        source=source,
        task_id=task_id or "",
    )


def finish_run(
    run,
    *,
    status,
    item_count=0,
    error_category="",
    new_count=None,
    known_count=None,
    known_updated_count=None,
    known_unchanged_count=None,
    listing_count=None,
    title_kept_count=None,
    title_discarded_count=None,
    details_requested_count=None,
    details_received_count=None,
    title_input_tokens=None,
    listing_fetch_duration_ms=None,
    title_preselection_duration_ms=None,
    detail_fetch_duration_ms=None,
    error_summary="",
):
    finished_at = timezone.now()
    run.status = status
    run.item_count = max(0, int(item_count or 0))
    run.finished_at = finished_at
    run.duration_ms = max(0, int((finished_at - run.started_at).total_seconds() * 1000))
    run.error_category = error_category[:80]
    run.new_count = new_count
    run.known_count = known_count
    run.known_updated_count = known_updated_count
    run.known_unchanged_count = known_unchanged_count
    run.listing_count = listing_count
    run.title_kept_count = title_kept_count
    run.title_discarded_count = title_discarded_count
    run.details_requested_count = details_requested_count
    run.details_received_count = details_received_count
    run.title_input_tokens = title_input_tokens
    run.listing_fetch_duration_ms = listing_fetch_duration_ms
    run.title_preselection_duration_ms = title_preselection_duration_ms
    run.detail_fetch_duration_ms = detail_fetch_duration_ms
    if error_summary:
        summary = error_summary[:240]
    elif error_category.startswith("omniroute.http_"):
        status_code = error_category.rsplit("_", 1)[-1]
        summary = f"OmniRoute respondió HTTP {status_code}." if status_code.isdigit() else "OmniRoute rechazó la solicitud."
    else:
        summary = SAFE_ERROR_SUMMARIES.get(error_category, "") if error_category else ""
    run.error_summary = summary
    run.save(update_fields=(
        "status", "item_count", "new_count", "known_count", "known_updated_count",
        "known_unchanged_count", "listing_count", "title_kept_count", "title_discarded_count",
        "details_requested_count", "details_received_count", "title_input_tokens",
        "listing_fetch_duration_ms", "title_preselection_duration_ms", "detail_fetch_duration_ms",
        "finished_at", "duration_ms", "error_category", "error_summary",
    ))
    log = logger.warning if status in {OperationalRun.Status.FAILED, OperationalRun.Status.RETRYING} else logger.info
    log(
        "operational_run kind=%s operation=%s source=%s status=%s duration_ms=%s item_count=%s error_category=%s",
        run.kind,
        run.operation,
        run.source or "-",
        run.status,
        run.duration_ms,
        run.item_count,
        run.error_category or "-",
    )
    return run


def acquire_refresh_lease(key, *, ttl_seconds=1200):
    """Claim a per-profile refresh lease shared by manual and scheduled tasks."""
    now = timezone.now()
    token = uuid.uuid4().hex
    with transaction.atomic():
        try:
            with transaction.atomic():
                RefreshLease.objects.create(
                    key=key, token=token, expires_at=now + timedelta(seconds=ttl_seconds),
                )
            return token
        except IntegrityError:
            lease = RefreshLease.objects.select_for_update().filter(key=key).first()
            if lease is None or lease.expires_at > now:
                return None
            lease.token = token
            lease.claimed = False
            lease.expires_at = now + timedelta(seconds=ttl_seconds)
            lease.save(update_fields=("token", "claimed", "expires_at"))
            return token


def release_refresh_lease(key, token):
    RefreshLease.objects.filter(key=key, token=token).delete()


def claim_refresh_lease(key, token, *, ttl_seconds=1200):
    now = timezone.now()
    return bool(RefreshLease.objects.filter(
        key=key, token=token, claimed=False, expires_at__gt=now,
    ).update(claimed=True, expires_at=now + timedelta(seconds=ttl_seconds)))


def release_refresh_lease_for_retry(key, token):
    RefreshLease.objects.filter(key=key, token=token).update(claimed=False)


def start_admin_command(command_id, profile_count):
    now = timezone.now()
    AdminCommandRun.objects.filter(pk=command_id, status=AdminCommandRun.Status.QUEUED).update(
        status=AdminCommandRun.Status.RUNNING,
        started_at=now,
        profile_count=profile_count,
    )


def record_admin_profile_result(command_id, *, results=None, failed=False):
    """Aggregate safe, per-source counts without storing profile or vacancy content."""
    with transaction.atomic():
        command = AdminCommandRun.objects.select_for_update().filter(
            pk=command_id, status=AdminCommandRun.Status.RUNNING,
        ).first()
        if command is None:
            return
        source_results = dict(command.source_results or {})
        for result in results or []:
            source = str(result.get("source", "unknown"))[:80]
            current = source_results.setdefault(source, {"queries": 0, "vacancies": 0, "failures": 0})
            current["queries"] += 1
            current["vacancies"] += max(0, int(result.get("count", 0) or 0))
            if not result.get("available", False):
                current["failures"] += 1
        command.source_results = source_results
        command.completed_profiles += 1
        if failed:
            command.failed_profiles += 1
        fields = ["source_results", "completed_profiles", "failed_profiles"]
        if command.completed_profiles >= command.profile_count:
            command.status = (
                AdminCommandRun.Status.FAILED if command.failed_profiles == command.profile_count
                else AdminCommandRun.Status.PARTIAL if command.failed_profiles or any(
                    values["failures"] for values in source_results.values()
                )
                else AdminCommandRun.Status.SUCCEEDED
            )
            command.finished_at = timezone.now()
            command.duration_ms = max(0, int((command.finished_at - command.started_at).total_seconds() * 1000))
            fields.extend(["status", "finished_at", "duration_ms"])
        command.save(update_fields=fields)

