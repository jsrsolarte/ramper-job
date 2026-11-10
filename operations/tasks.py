from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import AdminAuditEvent, AdminCommandRun, ApplicantActivity, OperationalRun
from .services import finish_run


@shared_task(name="operations.tasks.cleanup_operational_history")
def cleanup_operational_history(retention_days=90):
    now = timezone.now()
    stale_cutoff = now - timedelta(minutes=20)
    interrupted = 0
    for run in OperationalRun.objects.filter(
        status=OperationalRun.Status.RUNNING,
        started_at__lt=stale_cutoff,
    ).iterator():
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
