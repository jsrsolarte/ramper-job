from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models


def cv_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"profiles/{instance.owner_id}/cv/v{instance.revision_number}{suffix}"


class Profile(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_profile",
    )
    search_phrases = models.JSONField(default=list, blank=True)
    locations = models.JSONField(default=list, blank=True)
    remote_ok = models.BooleanField(default=False)
    min_score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="puntaje mínimo de compatibilidad",
    )
    cv_file = models.FileField(
        upload_to=cv_upload_path,
        blank=True,
        validators=[FileExtensionValidator(["pdf", "docx"])],
    )
    revision_number = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil laboral"
        verbose_name_plural = "perfiles laborales"

    def __str__(self):
        return f"Perfil de {self.owner.get_username()}"


class ProfileRevision(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="revisions")
    version = models.PositiveIntegerField()
    search_phrases = models.JSONField(default=list, blank=True)
    locations = models.JSONField(default=list, blank=True)
    remote_ok = models.BooleanField(default=False)
    cv_file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["profile", "version"], name="unique_profile_revision")
        ]
        verbose_name = "versión de perfil"
        verbose_name_plural = "versiones de perfil"

    def __str__(self):
        return f"{self.profile} · v{self.version}"


class GuidedTourProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Sin iniciar"
        IN_PROGRESS = "in_progress", "En curso"
        COMPLETED = "completed", "Completado"
        SKIPPED = "skipped", "Omitido"

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="guided_tour_progress",
    )
    version = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    current_step = models.CharField(max_length=40, blank=True)
    mandatory_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "progreso del recorrido inicial"
        verbose_name_plural = "progresos del recorrido inicial"

    def __str__(self):
        return f"Recorrido de {self.owner.get_username()} · {self.get_status_display()}"
