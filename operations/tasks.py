from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    AdminAuditEvent,
    AdminCommandRun,
    ApplicantActivity,
    OperationalRun,
    RefreshBatchProfile,
    RefreshWorkItem,
)
from .services import finish_run, release_refresh_lease, renew_refresh_lease


@shared_task(name="operations.tasks.cleanup_operational_history")
def cleanup_operational_history(retention_days=90):
    now = timezone.now()
    stale_cutoff = now - timedelta(minutes=20)
    interrupted = 0
    protected_run_ids = RefreshWorkItem.objects.exclude(
        status__in=(RefreshWorkItem.Status.SUCCEEDED, RefreshWorkItem.Status.PARTIAL, RefreshWorkItem.Status.FAILED),
    ).values_list("source_run_id", flat=True)
    protected_run_ids = list(protected_run_ids) + list(RefreshBatchProfile.objects.filter(
        finished_at__isnull=True,
    ).values_list("profile_run_id", flat=True))
    for run in OperationalRun.objects.filter(
        status=OperationalRun.Status.RUNNING,
        started_at__lt=stale_cutoff,
    ).exclude(pk__in=protected_run_ids).iterator():
        finish_run(run, status=OperationalRun.Status.FAILED, error_category="execution_interrupted")
        interrupted += 1

    cutoff = now - timedelta(days=max(90, int(retention_days)))
    deleted, _ = OperationalRun.objects.filter(started_at__lt=cutoff).delete()
    deleted_commands, _ = AdminCommandRun.objects.filter(requested_at__lt=cutoff).delete()
    return {
        "deleted_runs": deleted,
        "deleted_commands": deleted_commands,
        "interrupted_runs": interrupted,
    }


@shared_task(name="operations.tasks.reconcile_refresh_work")
def reconcile_refresh_work():
    """Recover queued units and close refreshes whose durable work has disappeared."""
    now = timezone.now()
    stale_cutoff = now - timedelta(minutes=20)
    dispatch_cutoff = now - timedelta(minutes=5)
    from jobs.resumable import (
        MAX_WORK_ATTEMPTS,
        _enqueue_work_item,
        _finish_batch_profile,
        _record_work_failure,
    )

    recovered = 0
    stale_item_ids = list(RefreshWorkItem.objects.filter(
        status=RefreshWorkItem.Status.RUNNING,
        heartbeat_at__lt=stale_cutoff,
    ).filter(models_q_lease_expired(now)).values_list("pk", flat=True))
    for item_id in stale_item_ids:
        exhausted_item = None
        with transaction.atomic():
            item = RefreshWorkItem.objects.select_for_update().filter(
                pk=item_id,
                status=RefreshWorkItem.Status.RUNNING,
            ).first()
            # Recheck under the row lock: a worker may have renewed its lease or
            # heartbeat after the initial stale-item query.
            if (
                item is None
                or item.heartbeat_at is None
                or item.heartbeat_at >= stale_cutoff
                or (item.lease_expires_at is not None and item.lease_expires_at > now)
            ):
                continue
            if item.attempts >= MAX_WORK_ATTEMPTS - 1:
                item.status = RefreshWorkItem.Status.FAILED
                item.phase = RefreshWorkItem.Phase.COMPLETE
                item.finished_at = now
                item.heartbeat_at = now
                item.lease_token = ""
                item.lease_expires_at = None
                item.error_category = "execution_interrupted"
                item.save(update_fields=(
                    "status", "phase", "finished_at", "heartbeat_at", "lease_token",
                    "lease_expires_at", "error_category",
                ))
                exhausted_item = item
            else:
                item.status = RefreshWorkItem.Status.QUEUED
                item.attempts += 1
                item.lease_token = ""
                item.lease_expires_at = None
                item.last_dispatched_at = None
                item.error_category = "execution_interrupted"
                item.save(update_fields=(
                    "status", "attempts", "lease_token", "lease_expires_at",
                    "last_dispatched_at", "error_category",
                ))
                recovered += 1
        if exhausted_item is not None:
            _record_work_failure(
                exhausted_item,
                status=RefreshWorkItem.Status.FAILED,
                error_category="execution_interrupted",
            )

    queued = RefreshWorkItem.objects.filter(status=RefreshWorkItem.Status.QUEUED).filter(
        models_q_dispatch_due(dispatch_cutoff),
    )
    dispatched = 0
    for item_id in queued.values_list("pk", flat=True)[:500]:
        _enqueue_work_item(item_id)
        dispatched += 1

    for batch_profile in RefreshBatchProfile.objects.filter(finished_at__isnull=True).iterator():
        if batch_profile.work_links.exclude(
            work_item__status__in=(
                RefreshWorkItem.Status.SUCCEEDED,
                RefreshWorkItem.Status.PARTIAL,
                RefreshWorkItem.Status.FAILED,
            ),
        ).exists():
            renew_refresh_lease(
                f"profile-refresh:{batch_profile.profile_id}",
                batch_profile.lease_token,
                ttl_seconds=24 * 60 * 60,
            )
        _finish_batch_profile(batch_profile.pk)

    stale_profiles = RefreshBatchProfile.objects.filter(
        finished_at__isnull=True,
        profile_run__started_at__lt=stale_cutoff,
    ).select_related("batch")
    for batch_profile in stale_profiles.iterator():
        if batch_profile.work_links.exclude(
            work_item__status__in=(
                RefreshWorkItem.Status.SUCCEEDED,
                RefreshWorkItem.Status.PARTIAL,
                RefreshWorkItem.Status.FAILED,
            ),
        ).exists():
            continue
        if not batch_profile.batch.planned_at:
            batch_profile.batch.planned_at = now
            batch_profile.batch.save(update_fields=("planned_at",))
        if not batch_profile.prepared_at:
            batch_profile.prepared_at = now
            batch_profile.failed = True
            batch_profile.save(update_fields=("prepared_at", "failed"))
        _finish_batch_profile(batch_profile.pk, failed=True)

    closed_commands = 0
    commands = AdminCommandRun.objects.filter(
        status__in=(AdminCommandRun.Status.QUEUED, AdminCommandRun.Status.RUNNING),
    ).filter(requested_at__lt=stale_cutoff)
    for command in commands.iterator():
        live_batches = command.refresh_batches.filter(
            status__in=("queued", "running"),
            heartbeat_at__gte=stale_cutoff,
        ).exists()
        live_units = RefreshWorkItem.objects.filter(
            batch__command=command,
            status__in=(RefreshWorkItem.Status.QUEUED, RefreshWorkItem.Status.RUNNING),
        ).exists()
        preparing_profiles = RefreshBatchProfile.objects.filter(
            batch__command=command,
            prepared_at__isnull=True,
            profile_run__started_at__gte=stale_cutoff,
        ).exists()
        if live_batches or live_units or preparing_profiles:
            continue
        for batch in command.refresh_batches.all():
            if not batch.planned_at:
                batch.planned_at = timezone.now()
                batch.save(update_fields=("planned_at",))
            for batch_profile in batch.profiles.filter(finished_at__isnull=True):
                if not batch_profile.prepared_at:
                    batch_profile.prepared_at = timezone.now()
                    batch_profile.failed = True
                    batch_profile.save(update_fields=("prepared_at", "failed"))
                _finish_batch_profile(batch_profile.pk, failed=True)
        command.refresh_from_db()
        if command.status not in (AdminCommandRun.Status.QUEUED, AdminCommandRun.Status.RUNNING):
            continue
        finished_at = timezone.now()
        command.status = AdminCommandRun.Status.PARTIAL if command.completed_profiles else AdminCommandRun.Status.FAILED
        command.finished_at = finished_at
        command.duration_ms = max(0, int((finished_at - (command.started_at or command.requested_at)).total_seconds() * 1000))
        command.error_summary = "La actualización se interrumpió y no quedan unidades activas."
        command.save(update_fields=("status", "finished_at", "duration_ms", "error_summary"))
        for batch_profile in RefreshBatchProfile.objects.filter(batch__command=command, finished_at__isnull=True):
            release_refresh_lease(f"profile-refresh:{batch_profile.profile_id}", batch_profile.lease_token)
        closed_commands += 1

    return {"recovered_units": recovered, "dispatched_units": dispatched, "closed_commands": closed_commands}


def models_q_lease_expired(now):
    from django.db.models import Q

    return Q(lease_expires_at__isnull=True) | Q(lease_expires_at__lte=now)


def models_q_dispatch_due(cutoff):
    from django.db.models import Q

    return Q(last_dispatched_at__isnull=True) | Q(last_dispatched_at__lte=cutoff)


@shared_task(name="operations.tasks.deactivate_inactive_applicants")
def deactivate_inactive_applicants(inactivity_days=7):
    User = get_user_model()
    now = timezone.now()
    cutoff = now - timedelta(days=max(1, int(inactivity_days)))
    applicant_ids = User.objects.filter(
        is_active=True,
        is_staff=False,
        is_superuser=False,
    ).values_list("pk", flat=True)
    deactivated = 0

    for user_id in applicant_ids.iterator():
        with transaction.atomic():
            user = User.objects.select_for_update().filter(
                pk=user_id,
                is_active=True,
                is_staff=False,
                is_superuser=False,
            ).first()
            if user is None:
                continue
            last_activity = ApplicantActivity.objects.filter(user_id=user.pk).values_list(
                "last_authenticated_activity", flat=True,
            ).first() or user.last_login or user.date_joined
            if last_activity is None or last_activity >= cutoff:
                continue
            user.is_active = False
            user.save(update_fields=("is_active",))
            AdminAuditEvent.objects.create(
                actor=None,
                target=user,
                action=AdminAuditEvent.Action.ACCOUNT_AUTO_DEACTIVATED,
            )
            deactivated += 1
    return {"deactivated_accounts": deactivated, "cutoff": cutoff.isoformat()}
