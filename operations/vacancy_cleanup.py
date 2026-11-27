"""Explicit, audited administrative removal of vacancy and analysis data."""

import hashlib
import secrets

from django.core import signing
from django.db import IntegrityError, transaction
from django.utils import timezone

from dashboard.models import RecommendationEvent, VacancyFollowUp
from jobs.models import ManualVacancySubmission, Vacancy, VacancyDetailLease
from matching.models import ProfileVacancyDiscovery, VacancyAnalysis, VacancyOrganization
from operations.models import (
    AdminAuditEvent,
    AdminCommandRun,
    OperationalParameter,
    OperationalRun,
    PeriodicRefreshState,
    RefreshBatch,
    RefreshWorkItem,
    VacancyCleanupConfirmation,
    VacancyCleanupOperation,
    VacancyDataCoverage,
    VacancyDataGeneration,
)
from operations.parameters import PROCESSING_PAUSED_KEY, set_processing_paused

CONFIRMATION_SALT = "ramper-vacancy-cleanup-confirmation-v1"
CONFIRMATION_MAX_AGE = 10 * 60
MAX_DRAIN_ATTEMPTS = 120


class CleanupError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def cleanup_preview_counts():
    return {
        "vacancies": Vacancy.objects.count(),
        "analyses": VacancyAnalysis.objects.count(),
        "organizations": VacancyOrganization.objects.count(),
        "discoveries": ProfileVacancyDiscovery.objects.count(),
        "follow_ups": VacancyFollowUp.objects.count(),
        "recommendation_events": RecommendationEvent.objects.count(),
        "manual_submissions": ManualVacancySubmission.objects.count(),
        "search_runs": OperationalRun.objects.count(),
        "refresh_batches": RefreshBatch.objects.count(),
        "work_items": RefreshWorkItem.objects.count(),
        "detail_leases": VacancyDetailLease.objects.count(),
        "refresh_commands": AdminCommandRun.objects.filter(command="refresh_sources").count(),
    }


def issue_cleanup_confirmation(counts):
    return signing.dumps({"counts": counts, "nonce": secrets.token_urlsafe(16)}, salt=CONFIRMATION_SALT)


def start_vacancy_cleanup(*, actor, token):
    try:
        signed = signing.loads(token, salt=CONFIRMATION_SALT, max_age=CONFIRMATION_MAX_AGE)
    except signing.BadSignature as exc:
        raise CleanupError("confirmation_expired") from exc
    current_counts = cleanup_preview_counts()
    if signed.get("counts") != current_counts:
        raise CleanupError("preview_changed")
    token_digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with transaction.atomic():
        try:
            confirmation = VacancyCleanupConfirmation.objects.create(
                token_digest=token_digest, requested_by=actor,
            )
        except IntegrityError as exc:
            raise CleanupError("confirmation_used") from exc
        control, _ = VacancyDataGeneration.objects.select_for_update().get_or_create(pk=1)
        if control.cleanup_active:
            raise CleanupError("cleanup_active")
        pause, _ = OperationalParameter.objects.select_for_update().get_or_create(
            key=PROCESSING_PAUSED_KEY, defaults={"value": 0},
        )
        was_paused = bool(pause.value)
        if not was_paused:
            set_processing_paused(actor=actor, paused=True)
            pause.refresh_from_db()
        operation = VacancyCleanupOperation.objects.create(
            requested_by=actor,
            status=VacancyCleanupOperation.Status.QUEUED,
            pause_was_active=was_paused,
            pause_parameter_updated_at=pause.updated_at,
            generation=control.generation + 1,
            counts={},
        )
        control.generation = operation.generation
        control.cleanup_active = True
        control.active_operation = operation
        control.save(update_fields=("generation", "cleanup_active", "active_operation", "updated_at"))
        # A consumed token is linked by its digest only; the token itself contains aggregate counts.
        confirmation.requested_by = actor
    try:
        from .tasks import execute_vacancy_cleanup_task

        execute_vacancy_cleanup_task.delay(operation.pk)
    except Exception as exc:
        VacancyCleanupOperation.objects.filter(pk=operation.pk).update(
            status=VacancyCleanupOperation.Status.FAILED,
            error_category="dispatch_failed",
        )
        raise CleanupError("dispatch_failed") from exc
    return operation


def _active_work_exists():
    return any((
        OperationalRun.objects.filter(status=OperationalRun.Status.RUNNING).exists(),
        RefreshWorkItem.objects.filter(status=RefreshWorkItem.Status.RUNNING).exists(),
        VacancyAnalysis.objects.filter(
            status=VacancyAnalysis.Status.PENDING,
            processing_started_at__isnull=False,
        ).exists(),
        VacancyOrganization.objects.filter(
            status=VacancyOrganization.Status.PENDING,
            processing_started_at__isnull=False,
        ).exists(),
        ManualVacancySubmission.objects.filter(status=ManualVacancySubmission.Status.PROCESSING).exists(),
    ))


def _delete_scoped_data():
    # Explicitly remove dependents first so all affected rows are countable and
    # protected profile and configuration rows cannot be reached by a cascade.
    VacancyAnalysis.objects.all().delete()
    VacancyOrganization.objects.all().delete()
    ProfileVacancyDiscovery.objects.all().delete()
    VacancyFollowUp.objects.all().delete()
    RecommendationEvent.objects.all().delete()
    ManualVacancySubmission.objects.all().delete()
    Vacancy.objects.all().delete()
    VacancyDetailLease.objects.all().delete()
    RefreshWorkItem.objects.all().delete()
    RefreshBatch.objects.all().delete()
    OperationalRun.objects.all().delete()
    AdminCommandRun.objects.filter(command="refresh_sources").delete()
    PeriodicRefreshState.objects.all().delete()


def execute_vacancy_cleanup(operation_id):
    operation = VacancyCleanupOperation.objects.filter(pk=operation_id).first()
    if operation is None or operation.status == VacancyCleanupOperation.Status.COMPLETED:
        return {"status": "missing_or_completed"}
    with transaction.atomic():
        control = VacancyDataGeneration.objects.select_for_update().filter(pk=1).first()
        operation = VacancyCleanupOperation.objects.select_for_update().get(pk=operation_id)
        if operation.status == VacancyCleanupOperation.Status.COMPLETED:
            return {"status": "missing_or_completed"}
        if control is None or not control.cleanup_active or control.active_operation_id != operation.pk:
            operation.status = VacancyCleanupOperation.Status.FAILED
            operation.error_category = "control_state_mismatch"
            operation.save(update_fields=("status", "error_category"))
            return {"status": "failed", "category": "control_state_mismatch"}
        operation.status = VacancyCleanupOperation.Status.RUNNING
        operation.started_at = operation.started_at or timezone.now()
        operation.attempt_count += 1
        operation.save(update_fields=("status", "started_at", "attempt_count"))
    if _active_work_exists():
        if operation.attempt_count >= MAX_DRAIN_ATTEMPTS:
            VacancyCleanupOperation.objects.filter(pk=operation.pk).update(
                status=VacancyCleanupOperation.Status.FAILED,
                error_category="active_work_timeout",
            )
            return {"status": "failed", "category": "active_work_timeout", "paused": True}
        VacancyCleanupOperation.objects.filter(pk=operation.pk).update(
            status=VacancyCleanupOperation.Status.WAITING,
        )
        from .tasks import execute_vacancy_cleanup_task

        execute_vacancy_cleanup_task.apply_async(args=(operation.pk,), countdown=15)
        return {"status": "waiting", "attempt": operation.attempt_count}

    try:
        with transaction.atomic():
            control = VacancyDataGeneration.objects.select_for_update().get(pk=1)
            operation = VacancyCleanupOperation.objects.select_for_update().get(pk=operation_id)
            if not control.cleanup_active or control.active_operation_id != operation.pk:
                raise CleanupError("control_state_mismatch")
            if _active_work_exists():
                raise CleanupError("work_resumed_during_cleanup")
            counts = cleanup_preview_counts()
            _delete_scoped_data()
            now = timezone.now()
            operation.counts = counts
            operation.status = VacancyCleanupOperation.Status.COMPLETED
            operation.finished_at = now
            operation.error_category = ""
            operation.save(update_fields=("counts", "status", "finished_at", "error_category"))
            VacancyDataCoverage.objects.update_or_create(
                pk=1, defaults={"covered_from": now, "cleanup_operation": operation},
            )
            control.generation += 1
            control.cleanup_active = False
            control.active_operation = None
            control.save(update_fields=("generation", "cleanup_active", "active_operation", "updated_at"))
            _restore_previous_pause(operation)
    except Exception:
        VacancyCleanupOperation.objects.filter(pk=operation_id).exclude(
            status=VacancyCleanupOperation.Status.COMPLETED,
        ).update(status=VacancyCleanupOperation.Status.FAILED, error_category="transaction_failed")
        return {"status": "failed", "category": "transaction_failed", "paused": True}
    return {"status": "completed", "counts": counts}


def _restore_previous_pause(operation):
    if operation.pause_was_active:
        return
    parameter = OperationalParameter.objects.select_for_update().filter(key=PROCESSING_PAUSED_KEY).first()
    if (
        parameter is not None
        and bool(parameter.value)
        and parameter.updated_at == operation.pause_parameter_updated_at
    ):
        set_processing_paused(actor=operation.requested_by, paused=False)
