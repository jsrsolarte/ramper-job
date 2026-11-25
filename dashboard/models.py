import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import timezone

from jobs.models import Vacancy
from profiles.models import Profile


class VacancyFollowUp(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente de decisión"
        DISCARDED = "discarded", "Descartada"
        APPLIED = "applied", "Aplicada"
        IN_PROGRESS = "in_progress", "En proceso"
        INTERVIEW = "interview", "Entrevista"
        FINALIZED = "finalized", "Finalizada"

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="vacancy_follow_ups")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="profile_follow_ups")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    previous_status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    state_changed_at = models.DateTimeField(default=timezone.now)
    archived_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "vacancy"], name="unique_follow_up_profile_vacancy")
        ]
        indexes = [
            models.Index(fields=["profile", "status"]),
            models.Index(fields=["archived_at", "state_changed_at"], name="followup_archive_due_idx"),
        ]
        ordering = ["-updated_at"]
        verbose_name = "seguimiento de vacante"
        verbose_name_plural = "seguimientos de vacantes"

    def __str__(self):
        return f"{self.profile} · {self.vacancy} · {self.get_status_display()}"


class RecommendationEvent(models.Model):
    """First time a vacancy becomes a visible recommendation for a profile."""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="recommendation_events")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="recommendation_events")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "vacancy"], name="unique_recommendation_event_profile_vacancy")
        ]
        indexes = [models.Index(fields=["profile", "created_at"], name="rec_event_profile_created_idx")]
        ordering = ["id"]

    def __str__(self):
        return f"Recomendación nueva · perfil {self.profile_id} · vacante {self.vacancy_id}"


class PushSubscription(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint_digest = models.CharField(max_length=64, unique=True)
    endpoint_ciphertext = models.TextField()
    p256dh_ciphertext = models.TextField()
    auth_ciphertext = models.TextField()
    active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(default=timezone.now)
    last_event_cutoff_id = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["profile", "active"], name="push_sub_profile_active_idx")]
        verbose_name = "suscripción de notificaciones"
        verbose_name_plural = "suscripciones de notificaciones"

    @staticmethod
    def _fernet():
        configured_key = getattr(settings, "PUSH_SUBSCRIPTION_ENCRYPTION_KEY", "")
        material = configured_key or settings.SECRET_KEY
        if not material:
            raise ImproperlyConfigured("Se requiere una clave estable para cifrar suscripciones push")
        derived = hashlib.sha256(b"ramper-push-subscription-v1:" + material.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(derived))

    @property
    def endpoint(self):
        return self._fernet().decrypt(self.endpoint_ciphertext.encode("ascii")).decode("utf-8")

    @endpoint.setter
    def endpoint(self, value):
        self.endpoint_ciphertext = self._fernet().encrypt(str(value).encode("utf-8")).decode("ascii")

    @property
    def p256dh_key(self):
        return self._fernet().decrypt(self.p256dh_ciphertext.encode("ascii")).decode("utf-8")

    @p256dh_key.setter
    def p256dh_key(self, value):
        self.p256dh_ciphertext = self._fernet().encrypt(str(value).encode("utf-8")).decode("ascii")

    @property
    def auth_key(self):
        return self._fernet().decrypt(self.auth_ciphertext.encode("ascii")).decode("utf-8")

    @auth_key.setter
    def auth_key(self, value):
        self.auth_ciphertext = self._fernet().encrypt(str(value).encode("utf-8")).decode("ascii")

    def __str__(self):
        return f"Suscripción push · perfil {self.profile_id}"


class PushDailyAttempt(models.Model):
    class Status(models.TextChoices):
        RESERVED = "reserved", "Reservado"
        SENT = "sent", "Aceptado por el servicio push"
        FAILED = "failed", "Fallido o resultado incierto"

    subscription = models.ForeignKey(
        PushSubscription,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="daily_attempts",
    )
    subscription_digest = models.CharField(max_length=64)
    local_date = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RESERVED)
    failure_category = models.CharField(max_length=32, blank=True)
    reserved_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["subscription_digest", "local_date"],
                name="unique_push_digest_local_day",
            )
        ]
        indexes = [models.Index(fields=["local_date", "status"], name="push_attempt_day_status_idx")]
        verbose_name = "intento de resumen push"
        verbose_name_plural = "intentos de resumen push"

    def __str__(self):
        return f"Intento push {self.local_date} · suscripción {self.subscription_id or 'eliminada'}"
