from django.conf import settings
from django.db import models
from django.utils import timezone


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
    class Status(models.TextChoices):
        QUEUED = "queued", "En cola"
        RUNNING = "running", "En curso"
        SUCCEEDED = "succeeded", "Completada"
        PARTIAL = "partial", "Parcial"
        FAILED = "failed", "Fallida"

    command = models.ForeignKey(
        AdminCommandRun, null=True, blank=True, on_delete=models.SET_NULL, related_name="refresh_batches",
    )
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
