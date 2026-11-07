from django.db import models
from django.db.models import Q
from django.utils import timezone

from jobs.models import Vacancy
from profiles.models import Profile, ProfileRevision

RUBRIC_VERSION = 2
PROMPT_VERSION = 4
CRITICAL_REQUIREMENT_DEDUCTION = "2.0"
RUBRIC_CRITERIA = {
    "skills": {
        "label": "Competencias y habilidades requeridas",
        "max_score": 4,
    },
    "experience": {
        "label": "Experiencia y responsabilidades relevantes",
        "max_score": 2,
    },
    "alignment": {
        "label": "Alineación del cargo o sector",
        "max_score": 2,
    },
    "education": {
        "label": "Educación o certificaciones requeridas",
        "max_score": 1,
    },
    "profile_criteria": {
        "label": "Otros criterios explícitos del perfil",
        "max_score": 1,
    },
}
RUBRIC_STATUSES = ("cumple", "parcial", "sin_evidencia", "contradicho", "no_aplica")


def default_matching_parameters():
    return {
        "temperature": 0.1,
        "rubric": {
            "version": RUBRIC_VERSION,
            "critical_requirement_deduction": CRITICAL_REQUIREMENT_DEDUCTION,
            "criteria": {
                "skills": {"max_score": 4, "description": "Competencias y habilidades requeridas"},
                "experience": {"max_score": 2, "description": "Experiencia y responsabilidades relevantes"},
                "alignment": {"max_score": 2, "description": "Alineación del cargo o sector"},
                "education": {"max_score": 1, "description": "Educación o certificaciones explícitamente requeridas"},
                "profile_criteria": {"max_score": 1, "description": "Otros criterios explícitos del perfil, sin ubicación"},
            },
        },
    }


DEFAULT_SEARCH_PROMPT = (
    "A partir del CV y las frases elegidas por la persona, sugiere hasta cinco términos "
    "adicionales de cargo, habilidad o especialidad respaldados por el CV. No repitas "
    "las frases de entrada, no inventes experiencia y devuelve únicamente JSON con la "
    'forma {"keywords": ["...", "..."]}.'
)


class MatchingConfig(models.Model):
    version = models.PositiveIntegerField(unique=True)
    rubric_version = models.PositiveSmallIntegerField(default=0)
    prompt_version = models.PositiveSmallIntegerField(default=1)
    search_prompt = models.TextField(default=DEFAULT_SEARCH_PROMPT)
    analysis_prompt = models.TextField()
    organization_prompt = models.TextField()
    parameters = models.JSONField(default=default_matching_parameters)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["is_active"], condition=Q(is_active=True), name="one_active_matching_config")
        ]
        verbose_name = "configuración de análisis"
        verbose_name_plural = "configuraciones de análisis"

    def __str__(self):
        return f"Configuración v{self.version}"


class ProfileSearchTerms(models.Model):
    profile_revision = models.ForeignKey(
        ProfileRevision, on_delete=models.CASCADE, related_name="search_term_sets"
    )
    matching_config = models.ForeignKey(
        MatchingConfig, on_delete=models.PROTECT, related_name="profile_search_terms"
    )
    keywords = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["profile_revision", "matching_config"],
                name="unique_search_terms_per_profile_revision_config",
            )
        ]
        verbose_name = "palabras de búsqueda de perfil"
        verbose_name_plural = "palabras de búsqueda de perfil"

    def __str__(self):
        return f"{self.profile_revision} · configuración v{self.matching_config.version}"


class ProfileVacancyDiscovery(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="vacancy_discoveries")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="profile_discoveries")
    first_found_at = models.DateTimeField(default=timezone.now)
    auto_discard_threshold = models.PositiveSmallIntegerField(default=0)
    auto_discard_evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "vacancy"], name="unique_profile_vacancy_discovery")]


class VacancyAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        COMPLETED = "completed", "Completo"
        FAILED = "failed", "Fallido"
        SUPERSEDED = "superseded", "Reemplazado"

    class OrganizationStatus(models.TextChoices):
        DEFERRED = "deferred", "Aún no elegible"
        PENDING = "pending", "Pendiente"
        COMPLETED = "completed", "Completo"
        FAILED = "failed", "Fallido"

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="analyses")
    profile_revision = models.ForeignKey(ProfileRevision, on_delete=models.PROTECT, related_name="analyses")
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="analyses")
    matching_config = models.ForeignKey(MatchingConfig, on_delete=models.PROTECT, related_name="analyses")
    organization = models.ForeignKey(
        "VacancyOrganization", null=True, blank=True, on_delete=models.SET_NULL, related_name="analyses"
    )
    organization_status = models.CharField(
        max_length=16, choices=OrganizationStatus.choices, default=OrganizationStatus.DEFERRED
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    organized_description = models.TextField(blank=True)
    organized_content = models.JSONField(default=dict, blank=True)
    score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    score_breakdown = models.JSONField(default=dict, blank=True)
    reasons = models.JSONField(default=list, blank=True)
    gaps = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_enqueued_at = models.DateTimeField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    recovery_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["profile", "status", "-created_at"]),
            models.Index(fields=["status", "last_enqueued_at"], name="matching_pending_enqueue_idx"),
            models.Index(fields=["status", "processing_started_at"], name="matching_processing_lease_idx"),
        ]
        verbose_name = "análisis de vacante"
        verbose_name_plural = "análisis de vacantes"

    def __str__(self):
        return f"{self.profile} · {self.vacancy}"


class VacancyOrganization(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        COMPLETED = "completed", "Completo"
        FAILED = "failed", "Fallido"

    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name="organizations")
    matching_config = models.ForeignKey(MatchingConfig, on_delete=models.PROTECT, related_name="organizations")
    content_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    content = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    last_enqueued_at = models.DateTimeField(null=True, blank=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    recovery_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["vacancy", "matching_config", "content_hash"], name="unique_vacancy_organization_version"
        )]
        indexes = [models.Index(fields=["status", "last_enqueued_at"], name="matching_org_enqueue_idx")]


class AICallAttempt(models.Model):
    class Stage(models.TextChoices):
        SCORING = "scoring", "Puntuación"
        ORGANIZATION = "organization", "Organización"

    class Outcome(models.TextChoices):
        SUCCEEDED = "succeeded", "Completado"
        RETRYING = "retrying", "Reintentando"
        FAILED = "failed", "Fallido"

    analysis = models.ForeignKey(
        VacancyAnalysis, null=True, blank=True, on_delete=models.CASCADE, related_name="ai_attempts"
    )
    organization = models.ForeignKey(
        VacancyOrganization, null=True, blank=True, on_delete=models.CASCADE, related_name="ai_attempts"
    )
    stage = models.CharField(max_length=16, choices=Stage.choices)
    duration_ms = models.PositiveIntegerField()
    outcome = models.CharField(max_length=16, choices=Outcome.choices)
    input_tokens = models.PositiveIntegerField(null=True, blank=True)
    output_tokens = models.PositiveIntegerField(null=True, blank=True)
    error_category = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(
            condition=(Q(analysis__isnull=False, organization__isnull=True)
                       | Q(analysis__isnull=True, organization__isnull=False)),
            name="ai_attempt_exactly_one_parent",
        )]
        indexes = [models.Index(fields=["stage", "outcome", "created_at"], name="ai_attempt_stage_idx")]
