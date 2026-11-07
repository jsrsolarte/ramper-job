from django.conf import settings
from django.db import models


class Vacancy(models.Model):
    class AvailabilityStatus(models.TextChoices):
        ACTIVE = "active", "Activa"
        CLOSED = "closed", "Cerrada"
        UNKNOWN = "unknown", "Desconocida"

    source = models.CharField(max_length=80)
    external_id = models.CharField(max_length=160, blank=True, null=True)
    dedupe_key = models.CharField(max_length=64, blank=True)
    title = models.CharField(max_length=400)
    company = models.CharField(max_length=300, blank=True, null=True)
    location = models.CharField(max_length=300, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    salary = models.CharField(max_length=200, blank=True, null=True)
    contract_type = models.CharField(max_length=200, blank=True, null=True)
    original_url = models.URLField(max_length=1000)
    published_at = models.DateTimeField(blank=True, null=True)
    raw_data = models.JSONField(default=dict, blank=True)
    availability_status = models.CharField(
        max_length=8,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.UNKNOWN,
        db_index=True,
    )
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-last_seen_at"]
        constraints = [
            models.UniqueConstraint(fields=["source", "original_url"], name="unique_source_vacancy_url"),
            models.UniqueConstraint(fields=["source", "dedupe_key"], name="unique_source_vacancy_identity"),
        ]
        indexes = [models.Index(fields=["source", "is_active"])]
        verbose_name = "vacante"
        verbose_name_plural = "vacantes"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.dedupe_key:
            from .identity import vacancy_dedupe_key

            self.dedupe_key = vacancy_dedupe_key(
                self.source,
                self.external_id,
                self.title,
                self.company,
                self.location,
                self.original_url,
            )
        super().save(*args, **kwargs)


class JobSourceStatus(models.Model):
    source = models.CharField(max_length=80, unique=True)
    available = models.BooleanField(default=False)
    status_message = models.CharField(max_length=300, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_vacancy_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "estado de fuente"
        verbose_name_plural = "estados de fuentes"

    def __str__(self):
        return self.source


class ManualVacancySubmission(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "En cola"
        PROCESSING = "processing", "Procesando"
        SCHEDULED = "scheduled", "Análisis programado"
        FAILED = "failed", "Fallido"

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="manual_vacancy_submissions",
    )
    title = models.CharField(max_length=400, blank=True)
    source = models.CharField(max_length=80, blank=True)
    original_url = models.URLField(max_length=1000)
    company = models.CharField(max_length=300, blank=True)
    location = models.CharField(max_length=300, blank=True)
    modality = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    salary = models.CharField(max_length=200, blank=True)
    contract_type = models.CharField(max_length=200, blank=True)
    vacancy = models.ForeignKey(
        Vacancy,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="manual_submissions",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    result_message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "registro manual de vacante"
        verbose_name_plural = "registros manuales de vacantes"

    def __str__(self):
        return f"{self.title} · {self.get_status_display()}"
