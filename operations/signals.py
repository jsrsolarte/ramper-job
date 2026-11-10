from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import ApplicantActivity


@receiver(post_save, sender=get_user_model())
def initialize_applicant_activity(sender, instance, created, **kwargs):
    if created and not instance.is_staff and not instance.is_superuser:
        ApplicantActivity.objects.get_or_create(
            user=instance,
            defaults={"last_authenticated_activity": instance.last_login or instance.date_joined or timezone.now()},
        )
