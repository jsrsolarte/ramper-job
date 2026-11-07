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
