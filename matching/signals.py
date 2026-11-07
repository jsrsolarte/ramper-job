from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from jobs.models import Vacancy


def _content_values(vacancy):
    return (
        vacancy.source, vacancy.title, vacancy.company, vacancy.location, vacancy.description,
        vacancy.salary, vacancy.contract_type, vacancy.original_url, vacancy.raw_data,
    )


@receiver(pre_save, sender=Vacancy)
def remember_vacancy_content(sender, instance, **kwargs):
    if not instance.pk:
        instance._organization_content_changed = False
        return
    previous = sender.objects.filter(pk=instance.pk).first()
    instance._organization_content_changed = bool(previous and _content_values(previous) != _content_values(instance))


@receiver(post_save, sender=Vacancy)
def refresh_vacancy_organizations(sender, instance, created, **kwargs):
    if created or not getattr(instance, "_organization_content_changed", False):
        return
    for analysis in instance.analyses.filter(
        status="completed", score__gte=0
    ).select_related("profile", "matching_config"):
        transaction.on_commit(lambda item_id=analysis.pk: _queue_current_organization(item_id))


def _queue_current_organization(analysis_id):
    from matching.models import VacancyAnalysis
    from matching.tasks import queue_organization

    analysis = VacancyAnalysis.objects.select_related("vacancy", "matching_config", "profile").filter(
        pk=analysis_id, status=VacancyAnalysis.Status.COMPLETED
    ).first()
    if analysis:
        queue_organization(analysis)
