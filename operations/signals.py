from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from celery import signals as celery_signals
from celery.exceptions import Ignore

from .models import ApplicantActivity, VacancyDataGeneration


@receiver(post_save, sender=get_user_model())
def initialize_applicant_activity(sender, instance, created, **kwargs):
    if created and not instance.is_staff and not instance.is_superuser:
        ApplicantActivity.objects.get_or_create(
            user=instance,
            defaults={"last_authenticated_activity": instance.last_login or instance.date_joined or timezone.now()},
        )


def _is_cleanup_sensitive_task(name):
    return (
        name.startswith("jobs.tasks.")
        or name.startswith("matching.tasks.")
        or name.startswith("dashboard.tasks.")
        or name == "operations.tasks.reconcile_refresh_work"
        or name == "operations.tasks.evaluate_operational_alerts"
    )


@celery_signals.before_task_publish.connect(weak=False, dispatch_uid="operations.vacancy_generation.publish")
def stamp_vacancy_generation(sender=None, headers=None, **kwargs):
    headers = headers if headers is not None else {}
    name = sender or (headers or {}).get("task", "")
    if not _is_cleanup_sensitive_task(name):
        return
    control, _ = VacancyDataGeneration.objects.get_or_create(pk=1)
    headers["ramper_data_generation"] = control.generation


@celery_signals.task_prerun.connect(weak=False, dispatch_uid="operations.vacancy_generation.guard")
def reject_stale_vacancy_task(sender=None, task=None, **kwargs):
    task_name = getattr(task, "name", "") or getattr(sender, "name", "") or ""
    if not _is_cleanup_sensitive_task(task_name) or task_name == "operations.tasks.execute_vacancy_cleanup":
        return
    request = getattr(task, "request", None)
    headers = getattr(request, "headers", None) or {}
    message_generation = headers.get("ramper_data_generation", 1)
    control, _ = VacancyDataGeneration.objects.get_or_create(pk=1)
    try:
        message_generation = int(message_generation)
    except (TypeError, ValueError):
        message_generation = 0
    if control.cleanup_active or message_generation != control.generation:
        raise Ignore()
