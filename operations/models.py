from datetime import time

from django.conf import settings
from django.db import models
from django.utils import timezone


class PeriodicRefreshState(models.Model):
    """Timestamp of the latest global automatic source-refresh cycle."""

    last_started_at = models.DateTimeField()


class AutomaticSearchSchedule(models.Model):
    """Global quiet window for automatic vacancy searches (Bogota local time)."""

    enabled = models.BooleanField(default=True)
    starts_at = models.TimeField(default=time(21, 0))
    ends_at = models.TimeField(default=time(7, 0))
    updated_at = models.DateTimeField(default=timezone.now)


class AutomaticSearchScheduleChange(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(default=timezone.now)
    previous_enabled = models.BooleanField()
    previous_starts_at = models.TimeField()
    previous_ends_at = models.TimeField()
    new_enabled = models.BooleanField()
    new_starts_at = models.TimeField()
    new_ends_at = models.TimeField()

    class Meta:
        ordering = ["-changed_at"]


class OperationalRun(models.Model):
    class Kind(models.TextChoices):
        INGESTION = "ingestion", "Consulta de fuentes"
        ANALYSIS = "analysis", "Análisis de vacante"
        RECOVERY = "recovery", "Recuperación de análisis"

    class Status(models.TextChoices):
        RUNNING = "running", "En curso"
        SUCCEEDED = "succeeded", "Completada"
        PARTIAL = "partial", "Parcial"
        RETRYING = "retrying", "Reintento"
        FAILED = "failed", "Fallida"

    kind = models.CharField(max_length=16, choices=Kind.choices)
    operation = models.CharField(max_length=80)
    source = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)
    item_count = models.PositiveIntegerField(default=0)
    new_count = models.PositiveIntegerField(null=True, blank=True)
    known_count = models.PositiveIntegerField(null=True, blank=True)
    known_updated_count = models.PositiveIntegerField(null=True, blank=True)
    known_unchanged_count = models.PositiveIntegerField(null=True, blank=True)
    listing_count = models.PositiveIntegerField(null=True, blank=True)
    title_kept_count = models.PositiveIntegerField(null=True, blank=True)
    title_discarded_count = models.PositiveIntegerField(null=True, blank=True)
    details_requested_count = models.PositiveIntegerField(null=True, blank=True)
    details_received_count = models.PositiveIntegerField(null=True, blank=True)
    details_reused_count = models.PositiveIntegerField(null=True, blank=True)
    title_input_tokens = models.PositiveIntegerField(null=True, blank=True)
    listing_fetch_duration_ms = models.PositiveIntegerField(null=True, blank=True)
    title_preselection_duration_ms = models.PositiveIntegerField(null=True, blank=True)
    detail_fetch_duration_ms = models.PositiveIntegerField(null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    error_category = models.CharField(max_length=80, blank=True)
    error_summary = models.CharField(max_length=240, blank=True)
    task_id = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["kind", "started_at"], name="ops_run_kind_started_idx"),
            models.Index(fields=["source", "started_at"], name="ops_run_source_started_idx"),
            models.Index(fields=["status", "started_at"], name="ops_run_status_started_idx"),
        ]
        verbose_name = "ejecución operativa"
        verbose_name_plural = "ejecuciones operativas"

    def __str__(self):
        return f"{self.operation} · {self.get_status_display()}"


class AdminCommandRun(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "En cola"
        RUNNING = "running", "En curso"
        SUCCEEDED = "succeeded", "Completada"
        PARTIAL = "partial", "Parcial"
        FAILED = "failed", "Fallida"

    command = models.CharField(max_length=80)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    requested_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    task_id = models.CharField(max_length=120, blank=True)
    profile_count = models.PositiveIntegerField(default=0)
    completed_profiles = models.PositiveIntegerField(default=0)
    failed_profiles = models.PositiveIntegerField(default=0)
    source_results = models.JSONField(default=dict, blank=True)
    error_summary = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["-requested_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["command"],
                condition=models.Q(status__in=["queued", "running"]),
                name="one_active_admin_command",
            ),
        ]

    def __str__(self):
        return f"{self.command} · {self.get_status_display()}"


class RefreshLease(models.Model):
    key = models.CharField(max_length=120, unique=True)
    token = models.CharField(max_length=120)
    claimed = models.BooleanField(default=False)
    expires_at = models.DateTimeField()


class RefreshBatch(models.Model):
    class Origin(models.TextChoices):
        AUTOMATIC = "automatic", "Automática"
        MANUAL = "manual", "Manual"

    class Status(models.TextChoices):
        QUEUED = "queued", "En cola"
        RUNNING = "running", "En curso"
        SUCCEEDED = "succeeded", "Completada"
        PARTIAL = "partial", "Parcial"
        FAILED = "failed", "Fallida"

    command = models.ForeignKey(
        AdminCommandRun, null=True, blank=True, on_delete=models.SET_NULL, related_name="refresh_batches",
    )
    # Existing batches are treated conservatively as automatic by the migration.
    origin = models.CharField(max_length=12, choices=Origin.choices, default=Origin.AUTOMATIC, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    heartbeat_at = models.DateTimeField(default=timezone.now, db_index=True)
    planned_at = models.DateTimeField(null=True, blank=True)


class RefreshBatchProfile(models.Model):
    batch = models.ForeignKey(RefreshBatch, on_delete=models.CASCADE, related_name="profiles")
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    profile_run = models.ForeignKey(OperationalRun, on_delete=models.CASCADE, related_name="refresh_profiles")
    lease_token = models.CharField(max_length=120)
    source_results = models.JSONField(default=dict, blank=True)
    found_vacancy_ids = models.JSONField(default=list, blank=True)
    search_request = models.JSONField(default=dict, blank=True)
    failed = models.BooleanField(default=False)
    stale = models.BooleanField(default=False)
    prepared_at = models.DateTimeField(null=True, blank=True, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "profile"], name="ops_refresh_batch_profile_uniq"),
        ]


class RefreshWorkItem(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "En cola"
        RUNNING = "running", "En curso"
        SUCCEEDED = "succeeded", "Completada"
        PARTIAL = "partial", "Parcial"
        FAILED = "failed", "Fallida"

    class Phase(models.TextChoices):
        TITLES = "titles", "Búsqueda"
        DETAILS = "details", "Fichas"
        COMPLETE = "complete", "Completada"

    batch = models.ForeignKey(RefreshBatch, on_delete=models.CASCADE, related_name="work_items")
    source_run = models.ForeignKey(OperationalRun, on_delete=models.CASCADE, related_name="refresh_work_items")
    source = models.CharField(max_length=80, db_index=True)
    identity = models.CharField(max_length=64)
    search_request = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED, db_index=True)
    phase = models.CharField(max_length=12, choices=Phase.choices, default=Phase.TITLES)
    cursor = models.PositiveIntegerField(default=0)
    listings = models.JSONField(default=list, blank=True)
    listing_count = models.PositiveIntegerField(default=0)
    title_kept_count = models.PositiveIntegerField(default=0)
    title_discarded_count = models.PositiveIntegerField(default=0)
    details_requested_count = models.PositiveIntegerField(default=0)
    details_received_count = models.PositiveIntegerField(default=0)
    details_reused_count = models.PositiveIntegerField(default=0)
    title_input_tokens = models.PositiveIntegerField(null=True, blank=True)
    available = models.BooleanField(default=True)
    error_category = models.CharField(max_length=80, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    lease_token = models.CharField(max_length=120, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    heartbeat_at = models.DateTimeField(default=timezone.now, db_index=True)
    last_dispatched_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["batch", "source", "identity"], name="ops_refresh_work_identity_uniq"),
        ]
        indexes = [
            models.Index(fields=["status", "lease_expires_at"], name="ops_refresh_work_lease_idx"),
            models.Index(fields=["batch", "status"], name="ops_ref_work_batch_state_idx"),
        ]


class RefreshWorkProfile(models.Model):
    work_item = models.ForeignKey(RefreshWorkItem, on_delete=models.CASCADE, related_name="profile_links")
    batch_profile = models.ForeignKey(RefreshBatchProfile, on_delete=models.CASCADE, related_name="work_links")
    revision_id = models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["work_item", "batch_profile"], name="ops_refresh_work_profile_uniq"),
        ]


class OperationalParameter(models.Model):
    key = models.CharField(max_length=80, unique=True)
    value = models.PositiveSmallIntegerField()
    updated_at = models.DateTimeField(default=timezone.now)


class ApplicantActivity(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applicant_activity",
    )
    last_authenticated_activity = models.DateTimeField(default=timezone.now, db_index=True)


class OperationalParameterChange(models.Model):
    key = models.CharField(max_length=80)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(default=timezone.now)
    previous_value = models.PositiveSmallIntegerField()
    new_value = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["-changed_at"]


class AdminAuditEvent(models.Model):
    class Action(models.TextChoices):
        ACCOUNT_CREATED = "account_created", "Cuenta creada"
        ACCOUNT_DEACTIVATED = "account_deactivated", "Cuenta desactivada"
        ACCOUNT_AUTO_DEACTIVATED = "account_auto_deactivated", "Desactivada por inactividad"
        ACCOUNT_REACTIVATED = "account_reactivated", "Cuenta reactivada"
        INVITATION_CREATED = "invitation_created", "Invitación creada"
        INVITATION_REVOKED = "invitation_revoked", "Invitación revocada"
        INVITATION_ACCEPTED = "invitation_accepted", "Invitación aceptada"
        PASSWORD_RESET_REQUESTED = "password_reset_requested", "Recuperación solicitada"
        PASSWORD_RESET_DELIVERY_FAILED = "password_reset_delivery_failed", "Fallo de entrega de recuperación"
        PASSWORD_RESET_LINK_GENERATED = "password_reset_link_generated", "Enlace de restablecimiento generado"
        PASSWORD_RESET_UNAVAILABLE = "password_reset_unavailable", "Recuperación no disponible"
        PROCESSING_PAUSED = "processing_paused", "Procesamiento pausado"
        PROCESSING_RESUMED = "processing_resumed", "Procesamiento reanudado"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="admin_audit_actions",
        null=True,
        blank=True,
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="admin_audit_events",
        null=True,
        blank=True,
    )
    invitation = models.ForeignKey(
        "UserInvitation",
        on_delete=models.SET_NULL,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    invitation_email = models.EmailField(blank=True)
    action = models.CharField(max_length=40, choices=Action.choices)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} · {self.created_at:%Y-%m-%d %H:%M}"


class UserInvitation(models.Model):
    email = models.EmailField()
    token_hash = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_user_invitations",
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "created_at"], name="ops_invite_email_created_idx"),
            models.Index(fields=["expires_at", "used_at"], name="ops_invite_expiry_used_idx"),
        ]

    def __str__(self):
        return f"Invitación para {self.email}"

    def is_pending(self, *, at=None):
        at = at or timezone.now()
        return self.used_at is None and self.revoked_at is None and self.expires_at > at


class OperationalAlertState(models.Model):
    """Singleton health and activation record for the internal evaluator."""

    activated_at = models.DateTimeField(default=timezone.now)
    last_started_at = models.DateTimeField(null=True, blank=True)
    last_succeeded_at = models.DateTimeField(null=True, blank=True)
    last_error_category = models.CharField(max_length=40, blank=True)


class OperationalIncident(models.Model):
    class Kind(models.TextChoices):
        RECURRING_FAILURE = "recurring_failure", "Fallos recurrentes"
        NO_PROGRESS = "no_progress", "Trabajo sin progreso"
        PERIODIC_OVERDUE = "periodic_overdue", "Ciclo retrasado"

    class Status(models.TextChoices):
        OPEN = "open", "Activo"
        ACKNOWLEDGED = "acknowledged", "Reconocido"
        RECOVERED = "recovered", "Recuperado"

    kind = models.CharField(max_length=24, choices=Kind.choices)
    component = models.CharField(max_length=32)
    category = models.CharField(max_length=48)
    first_observed_at = models.DateTimeField()
    last_observed_at = models.DateTimeField()
    count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    consecutive_clear_checks = models.PositiveSmallIntegerField(default=0)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="acknowledged_operational_incidents",
    )
    recovered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_observed_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "component", "category"],
                condition=models.Q(status__in=["open", "acknowledged"]),
                name="one_active_operational_incident_key",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "last_observed_at"], name="ops_incident_status_seen_idx"),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.component} · {self.get_status_display()}"


class OperationalAlertSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="operational_alert_subscriptions",
    )
    endpoint_digest = models.CharField(max_length=64, unique=True)
    endpoint_ciphertext = models.TextField()
    p256dh_ciphertext = models.TextField()
    auth_ciphertext = models.TextField()
    active = models.BooleanField(default=False)
    consented_at = models.DateTimeField(null=True, blank=True)
    last_notified_incident_id = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def _fernet():
        # Keep the same encryption key and format as applicant push subscriptions.
        from dashboard.models import PushSubscription

        return PushSubscription._fernet()

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


class OperationalAlertPushAttempt(models.Model):
    class Status(models.TextChoices):
        RESERVED = "reserved", "Reservado"
        SENT = "sent", "Aceptado por el servicio push"
        FAILED = "failed", "Fallido o resultado incierto"

    subscription = models.ForeignKey(
        OperationalAlertSubscription,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="push_attempts",
    )
    subscription_digest = models.CharField(max_length=64)
    latest_incident_id = models.PositiveBigIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RESERVED)
    failure_category = models.CharField(max_length=32, blank=True)
    reserved_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["subscription_digest", "reserved_at"], name="ops_push_digest_reserved_idx"),
        ]


class VacancyDataGeneration(models.Model):
    generation = models.PositiveBigIntegerField(default=1)
    cleanup_active = models.BooleanField(default=False)
    active_operation = models.ForeignKey(
        "VacancyCleanupOperation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="active_generation_states",
    )
    updated_at = models.DateTimeField(auto_now=True)


class VacancyDataCoverage(models.Model):
    covered_from = models.DateTimeField(default=timezone.now)
    cleanup_operation = models.ForeignKey(
        "VacancyCleanupOperation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="coverage_records",
    )


class VacancyCleanupOperation(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "En espera"
        RUNNING = "running", "En curso"
        WAITING = "waiting", "Esperando trabajo activo"
        COMPLETED = "completed", "Completada"
        FAILED = "failed", "Fallida; pausada para recuperación"

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="vacancy_cleanups",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.QUEUED)
    requested_at = models.DateTimeField(default=timezone.now, editable=False)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    pause_was_active = models.BooleanField(default=False)
    pause_parameter_updated_at = models.DateTimeField(null=True, blank=True)
    generation = models.PositiveBigIntegerField(default=1)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    counts = models.JSONField(default=dict, blank=True)
    error_category = models.CharField(max_length=40, blank=True)


class VacancyCleanupConfirmation(models.Model):
    token_digest = models.CharField(max_length=64, unique=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
