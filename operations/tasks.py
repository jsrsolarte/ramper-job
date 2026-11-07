from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import AdminCommandRun, OperationalRun
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
