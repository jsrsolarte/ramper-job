import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.http import require_POST

from jobs.models import JobSourceStatus, ManualVacancySubmission
from jobs.tasks import process_manual_vacancy_submission
from matching.models import AICallAttempt, VacancyAnalysis

from .decorators import platform_admin_required
from .forms import (
    ApplicantCreationForm,
    InvitationAcceptanceForm,
    InvitationEmailForm,
    ManualVacancySubmissionForm,
)
from .models import (
    AdminAuditEvent,
    AdminCommandRun,
    OperationalParameterChange,
    OperationalRun,
    UserInvitation,
)
from .parameters import (
    AUTO_DISCARD_DAYS_KEY,
    DEFAULT_AUTO_DISCARD_DAYS,
    DEFAULT_FOLLOW_UP_ARCHIVE_DAYS,
    FOLLOW_UP_ARCHIVE_DAYS_KEY,
    MAX_RETENTION_DAYS,
    MAX_REFRESH_MINUTES,
    MIN_RETENTION_DAYS,
    MIN_REFRESH_MINUTES,
    REFRESH_INTERVAL_KEY,
    current_auto_discard_days,
    current_follow_up_archive_days,
    current_refresh_interval_minutes,
    initial_refresh_interval_minutes,
    reset_refresh_interval,
    save_parameter,
    save_refresh_interval,
)
from .platform_statistics import build_platform_statistics

PERIODS = {"24h": ("24 horas", timedelta(hours=24)), "7d": ("7 días", timedelta(days=7)), "30d": ("30 días", timedelta(days=30))}
ALLOWED_COMMANDS = {"refresh_sources": "Actualizar fuentes ahora"}
logger = logging.getLogger(__name__)


@platform_admin_required
def admin_center(request):
    return render(request, "operations/admin_center.html", {
        "applicant_count": get_user_model().objects.filter(is_superuser=False, is_staff=False).count(),
    })


@platform_admin_required
def manual_vacancies(request):
    if request.method == "POST":
        form = ManualVacancySubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.submitted_by = request.user
            submission.save()
            try:
                process_manual_vacancy_submission.delay(submission.pk)
            except Exception as exc:
                submission.status = ManualVacancySubmission.Status.FAILED
                submission.result_message = "No fue posible poner el registro en cola. Puedes volver a intentarlo."
                submission.save(update_fields=("status", "result_message", "updated_at"))
                logger.error(
                    "manual_vacancy_dispatch_failed submission_id=%s exception_type=%s",
                    submission.pk,
                    type(exc).__name__,
                )
                messages.error(request, submission.result_message)
            else:
                messages.success(request, "Vacante recibida. El procesamiento continuará en segundo plano.")
            return redirect("operations:manual_vacancies")
    else:
        form = ManualVacancySubmissionForm()
    return render(request, "operations/manual_vacancies.html", {
        "form": form,
        "submissions": ManualVacancySubmission.objects.select_related(
            "submitted_by", "vacancy",
        )[:25],
    })


@platform_admin_required
def platform_statistics(request):
    period = request.GET.get("period", "30d")
    return render(request, "operations/platform_statistics.html", build_platform_statistics(period=period))


@platform_admin_required
def users(request):
    User = get_user_model()
    accounts = User.objects.filter(is_superuser=False, is_staff=False).order_by("username")
    return render(request, "operations/users.html", {
        "accounts": accounts,
        "invitations": UserInvitation.objects.select_related("created_by")[:30],
        "now": timezone.now(),
        "audit_events": AdminAuditEvent.objects.select_related("actor", "target")[:30],
    })


@platform_admin_required
def create_invitation(request):
    if request.method != "POST":
        return redirect("operations:users")
    form = InvitationEmailForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Escribe un correo válido para generar la invitación.")
        return redirect("operations:users")

    email = form.cleaned_data["email"].strip()
    raw_token = secrets.token_urlsafe(32)
    now = timezone.now()
    with transaction.atomic():
        # Serialize invitation replacement even when no previous invitation exists yet.
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        previous_invitations = list(UserInvitation.objects.select_for_update().filter(
            email__iexact=email, used_at__isnull=True, revoked_at__isnull=True,
        ))
        UserInvitation.objects.filter(pk__in=[item.pk for item in previous_invitations]).update(revoked_at=now)
        for previous in previous_invitations:
            AdminAuditEvent.objects.create(
                actor=request.user,
                action=AdminAuditEvent.Action.INVITATION_REVOKED,
                invitation=previous,
                invitation_email=previous.email,
            )
        invitation = UserInvitation.objects.create(
            email=email,
            token_hash=hashlib.sha256(raw_token.encode("utf-8")).hexdigest(),
            created_by=request.user,
            expires_at=now + timedelta(days=7),
        )
        AdminAuditEvent.objects.create(
            actor=request.user,
            action=AdminAuditEvent.Action.INVITATION_CREATED,
            invitation=invitation,
            invitation_email=email,
        )

    invitation_url = request.build_absolute_uri(reverse("invitation_accept")) + f"#{raw_token}"
    response = render(request, "operations/invitation_link.html", {
        "invitation": invitation,
        "invitation_url": invitation_url,
    })
    response["Cache-Control"] = "private, no-store"
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


@platform_admin_required
def revoke_invitation(request, invitation_id):
    if request.method != "POST":
        return redirect("operations:users")
    with transaction.atomic():
        invitation = get_object_or_404(UserInvitation.objects.select_for_update(), pk=invitation_id)
        if invitation.is_pending():
            invitation.revoked_at = timezone.now()
            invitation.save(update_fields=("revoked_at",))
            AdminAuditEvent.objects.create(
                actor=request.user,
                action=AdminAuditEvent.Action.INVITATION_REVOKED,
                invitation=invitation,
                invitation_email=invitation.email,
            )
            revoked = True
        else:
            revoked = False
    if revoked:
        messages.success(request, "Se revocó la invitación.")
    else:
        messages.info(request, "La invitación ya no está pendiente.")
    return redirect("operations:users")


def _invitation_for_token(raw_token):
    if not raw_token or len(raw_token) > 128:
        return None
    digest = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    invitation = UserInvitation.objects.filter(token_hash=digest).first()
    return invitation if invitation and invitation.is_pending() else None


def invitation_accept(request):
    if request.method == "GET":
        response = render(request, "operations/invitation_accept.html", {
            "acceptance_form": InvitationAcceptanceForm(),
            "acceptance_url": reverse("invitation_accept"),
            "validation_url": reverse("invitation_validate"),
        })
        response["Cache-Control"] = "private, no-store"
        response["Referrer-Policy"] = "no-referrer"
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    raw_token = request.POST.get("token", "")
    invitation = _invitation_for_token(raw_token)
    if invitation is None:
        response = render(request, "operations/invitation_accept.html", {
            "acceptance_form": InvitationAcceptanceForm(),
            "invalid_invitation": True,
            "acceptance_url": reverse("invitation_accept"),
            "validation_url": reverse("invitation_validate"),
        }, status=400)
        response["Cache-Control"] = "private, no-store"
        response["Referrer-Policy"] = "no-referrer"
        return response

    form = InvitationAcceptanceForm(request.POST)
    if not form.is_valid():
        response = render(request, "operations/invitation_accept.html", {
            "acceptance_form": form,
            "invitation_email": invitation.email,
            "token_for_form": raw_token,
            "acceptance_url": reverse("invitation_accept"),
            "validation_url": reverse("invitation_validate"),
        })
        response["Cache-Control"] = "private, no-store"
        response["Referrer-Policy"] = "no-referrer"
        return response

    User = get_user_model()
    try:
        with transaction.atomic():
            locked_invitation = UserInvitation.objects.select_for_update().filter(
                pk=invitation.pk,
            ).first()
            if locked_invitation is None or not locked_invitation.is_pending():
                response = render(request, "operations/invitation_accept.html", {
                    "acceptance_form": form,
                    "invalid_invitation": True,
                    "acceptance_url": reverse("invitation_accept"),
                    "validation_url": reverse("invitation_validate"),
                }, status=400)
                response["Cache-Control"] = "private, no-store"
                response["Referrer-Policy"] = "no-referrer"
                return response
            applicant = form.save(commit=False)
            applicant.email = locked_invitation.email
            applicant.is_active = True
            applicant.is_staff = False
            applicant.is_superuser = False
            applicant.save()
            locked_invitation.used_at = timezone.now()
            locked_invitation.save(update_fields=("used_at",))
            AdminAuditEvent.objects.create(
                actor=locked_invitation.created_by,
                target=applicant,
                invitation=locked_invitation,
                invitation_email=locked_invitation.email,
                action=AdminAuditEvent.Action.INVITATION_ACCEPTED,
            )
    except IntegrityError:
        form.add_error("username", "Ese nombre de usuario ya está en uso. Elige otro.")
        response = render(request, "operations/invitation_accept.html", {
            "acceptance_form": form,
            "invitation_email": invitation.email,
            "token_for_form": raw_token,
            "acceptance_url": reverse("invitation_accept"),
            "validation_url": reverse("invitation_validate"),
        })
        response["Cache-Control"] = "private, no-store"
        response["Referrer-Policy"] = "no-referrer"
        return response

    messages.success(request, "Tu cuenta quedó creada. Ya puedes iniciar sesión.")
    return redirect("login")


@require_POST
def validate_invitation(request):
    raw_token = request.POST.get("token", "")
    invitation = _invitation_for_token(raw_token)
    if invitation is None:
        response = JsonResponse({"valid": False}, status=400)
    else:
        response = JsonResponse({"valid": True, "email": invitation.email})
    response["Cache-Control"] = "private, no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


@platform_admin_required
def create_user(request):
    if request.method == "POST":
        form = ApplicantCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                applicant = form.save(commit=False)
                applicant.is_staff = False
                applicant.is_superuser = False
                applicant.save()
                AdminAuditEvent.objects.create(
                    actor=request.user, target=applicant,
                    action=AdminAuditEvent.Action.ACCOUNT_CREATED,
                )
            messages.success(request, "La cuenta del aspirante quedó creada.")
            return redirect("operations:users")
    else:
        form = ApplicantCreationForm()
    return render(request, "operations/user_form.html", {"form": form})


@platform_admin_required
def toggle_user(request, user_id):
    if request.method != "POST":
        return redirect("operations:users")
    User = get_user_model()
    applicant = get_object_or_404(
        User.objects.filter(is_superuser=False, is_staff=False), pk=user_id,
    )
    active = request.POST.get("active")
    if active not in {"true", "false"}:
        messages.error(request, "La acción solicitada no es válida.")
        return redirect("operations:users")
    new_state = active == "true"
    if applicant.is_active != new_state:
        applicant.is_active = new_state
        applicant.save(update_fields=("is_active",))
        AdminAuditEvent.objects.create(
            actor=request.user,
            target=applicant,
            action=(AdminAuditEvent.Action.ACCOUNT_REACTIVATED if new_state
                    else AdminAuditEvent.Action.ACCOUNT_DEACTIVATED),
        )
        messages.success(request, "Se reactivó la cuenta." if new_state else "Se desactivó la cuenta.")
    return redirect("operations:users")


@platform_admin_required
def request_password_reset(request, user_id):
    if request.method != "POST":
        return redirect("operations:users")
    User = get_user_model()
    applicant = get_object_or_404(
        User.objects.filter(is_superuser=False, is_staff=False), pk=user_id,
    )
    if not applicant.is_active or not applicant.has_usable_password():
        AdminAuditEvent.objects.create(
            actor=request.user,
            target=applicant,
            action=AdminAuditEvent.Action.PASSWORD_RESET_UNAVAILABLE,
        )
        messages.error(request, "Solo se puede generar un enlace para una cuenta activa con contraseña.")
        return redirect("operations:users")

    uidb64 = urlsafe_base64_encode(force_bytes(applicant.pk))
    token = default_token_generator.make_token(applicant)
    reset_url = request.build_absolute_uri(reverse(
        "password_reset_confirm", kwargs={"uidb64": uidb64, "token": token},
    ))
    AdminAuditEvent.objects.create(
        actor=request.user,
        target=applicant,
        action=AdminAuditEvent.Action.PASSWORD_RESET_LINK_GENERATED,
    )
    response = render(request, "operations/password_reset_link.html", {
        "applicant": applicant,
        "reset_url": reset_url,
        "timeout_minutes": max(1, settings.PASSWORD_RESET_TIMEOUT // 60),
    })
    response["Cache-Control"] = "private, no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


def _enqueue_refresh(command_id):
    from jobs.tasks import refresh_sources

    try:
        task = refresh_sources.delay(command_id)
        AdminCommandRun.objects.filter(pk=command_id).update(task_id=task.id or "")
    except Exception:
        command = AdminCommandRun.objects.filter(pk=command_id).first()
        if command:
            now = timezone.now()
            command.status = AdminCommandRun.Status.FAILED
            command.error_summary = "No fue posible poner la actualización en cola."
            command.started_at = now
            command.finished_at = now
            command.duration_ms = 0
            command.save(update_fields=("status", "error_summary", "started_at", "finished_at", "duration_ms"))


@platform_admin_required
def run_command(request):
    if request.method != "POST":
        return redirect("operations:dashboard")
    if set(request.POST.keys()) - {"command", "csrfmiddlewaretoken"}:
        return render(request, "operations/invalid_command.html", status=400)
    command_name = request.POST.get("command", "")
    if command_name not in ALLOWED_COMMANDS:
        return render(request, "operations/invalid_command.html", status=400)

    try:
        with transaction.atomic():
            command = AdminCommandRun.objects.create(command=command_name, requested_by=request.user)
            transaction.on_commit(lambda command_id=command.pk: _enqueue_refresh(command_id))
        messages.success(request, "La actualización quedó en cola.")
    except IntegrityError:
        messages.info(request, "Ya hay una actualización manual en cola o en curso.")
    return redirect("operations:dashboard")


@platform_admin_required
def parameters(request):
    error = ""
    if request.method == "POST":
        if set(request.POST.keys()) - {"parameter", "value", "action", "csrfmiddlewaretoken"}:
            error = "La solicitud contiene campos que no están habilitados."
        elif request.POST.get("parameter") not in {
            REFRESH_INTERVAL_KEY, AUTO_DISCARD_DAYS_KEY, FOLLOW_UP_ARCHIVE_DAYS_KEY,
        }:
            error = "El parámetro solicitado no está disponible."
        elif request.POST.get("parameter") == REFRESH_INTERVAL_KEY and request.POST.get("action") == "reset":
            reset_refresh_interval(actor=request.user)
            messages.success(request, "Se restauró el intervalo inicial. El cambio aplicará en los siguientes ciclos.")
            return redirect("operations:parameters")
        elif request.POST.get("action") == "save":
            parameter_key = request.POST.get("parameter")
            raw_value = request.POST.get("value", "")
            if not raw_value.isdecimal():
                unit = "minutos" if parameter_key == REFRESH_INTERVAL_KEY else "días"
                error = f"Ingresa un número entero de {unit}."
            else:
                value = int(raw_value)
                if parameter_key == REFRESH_INTERVAL_KEY and not MIN_REFRESH_MINUTES <= value <= MAX_REFRESH_MINUTES:
                    error = f"El intervalo debe estar entre {MIN_REFRESH_MINUTES} y {MAX_REFRESH_MINUTES} minutos."
                elif parameter_key != REFRESH_INTERVAL_KEY and not MIN_RETENTION_DAYS <= value <= MAX_RETENTION_DAYS:
                    error = f"El plazo debe estar entre {MIN_RETENTION_DAYS} y {MAX_RETENTION_DAYS} días."
                else:
                    if parameter_key == REFRESH_INTERVAL_KEY:
                        save_refresh_interval(actor=request.user, value_minutes=value)
                        messages.success(request, "Se guardó el intervalo. No se inició una búsqueda; aplicará en los siguientes ciclos.")
                    else:
                        save_parameter(actor=request.user, key=parameter_key, value=value)
                        messages.success(request, "Se guardó el plazo. No se inició una tarea; aplicará en la siguiente ejecución diaria.")
                    return redirect("operations:parameters")
        else:
            error = "Selecciona una acción disponible."

    context = admin.site.each_context(request)
    context.update({
        "current_interval": current_refresh_interval_minutes(),
        "initial_interval": initial_refresh_interval_minutes(),
        "min_interval": MIN_REFRESH_MINUTES,
        "max_interval": MAX_REFRESH_MINUTES,
        "auto_discard_days": current_auto_discard_days(),
        "initial_auto_discard_days": DEFAULT_AUTO_DISCARD_DAYS,
        "follow_up_archive_days": current_follow_up_archive_days(),
        "initial_follow_up_archive_days": DEFAULT_FOLLOW_UP_ARCHIVE_DAYS,
        "min_retention_days": MIN_RETENTION_DAYS,
        "max_retention_days": MAX_RETENTION_DAYS,
        "history": OperationalParameterChange.objects.select_related("changed_by")[:20],
        "error": error,
    })
    return render(request, "operations/parameters.html", context, status=400 if error else 200)


@platform_admin_required
def dashboard(request):
    period = request.GET.get("period", "24h")
    if period not in PERIODS:
        period = "24h"
    period_label, duration = PERIODS[period]
    now = timezone.now()
    since = now - duration
    runs = OperationalRun.objects.filter(started_at__gte=since, started_at__lte=now)

    def summarize(queryset):
        result = queryset.aggregate(
            total=Count("pk"),
            succeeded=Count("pk", filter=Q(status=OperationalRun.Status.SUCCEEDED)),
            partial=Count("pk", filter=Q(status=OperationalRun.Status.PARTIAL)),
            retrying=Count("pk", filter=Q(status=OperationalRun.Status.RETRYING)),
            failed=Count("pk", filter=Q(status=OperationalRun.Status.FAILED)),
            items=Sum("item_count"),
            average_duration=Avg("duration_ms", filter=Q(finished_at__isnull=False)),
        )
        result["items"] = result["items"] or 0
        result["average_duration"] = round(result["average_duration"] or 0)
        result["failure_rate"] = round(100 * result["failed"] / result["total"]) if result["total"] else 0
        return result

    source_summaries = {}
    source_names = runs.filter(kind=OperationalRun.Kind.INGESTION, source__gt="").values_list(
        "source", flat=True
    ).distinct()
    for source in source_names:
        source_runs = runs.filter(kind=OperationalRun.Kind.INGESTION, source=source)
        summary = summarize(source_runs)
        summary.update({
            "source": source,
            "last_success": source_runs.filter(status=OperationalRun.Status.SUCCEEDED).order_by(
                "-started_at"
            ).values_list("started_at", flat=True).first(),
            "last_error": source_runs.filter(
                status__in=(OperationalRun.Status.FAILED, OperationalRun.Status.RETRYING)
            ).order_by("-started_at").values_list("error_summary", flat=True).first(),
        })
        source_summaries[source] = summary

    source_rows = []
    for source in JobSourceStatus.objects.order_by("source"):
        source_rows.append({
            "status": source,
            "metrics": source_summaries.get(source.source, {
                "total": 0, "failed": 0, "average_duration": 0, "last_error": "",
            }),
        })

    pending = VacancyAnalysis.objects.filter(status=VacancyAnalysis.Status.PENDING)
    oldest_pending = pending.order_by("created_at").values_list("created_at", flat=True).first()
    latest_errors = runs.filter(
        status__in=(OperationalRun.Status.FAILED, OperationalRun.Status.RETRYING),
    ).exclude(error_summary="").order_by("-started_at")[:10]
    coverage_start = OperationalRun.objects.order_by("started_at").values_list("started_at", flat=True).first()
    ai_call_stages = []
    for stage, label in AICallAttempt.Stage.choices:
        metric = AICallAttempt.objects.filter(stage=stage, created_at__gte=since, created_at__lte=now).aggregate(
            total=Count("pk"),
            succeeded=Count("pk", filter=Q(outcome=AICallAttempt.Outcome.SUCCEEDED)),
            retrying=Count("pk", filter=Q(outcome=AICallAttempt.Outcome.RETRYING)),
            failed=Count("pk", filter=Q(outcome=AICallAttempt.Outcome.FAILED)),
            average_duration=Avg("duration_ms"),
            input_tokens=Sum("input_tokens"),
            output_tokens=Sum("output_tokens"),
        )
        ai_call_stages.append({"label": label, **metric})

    context = admin.site.each_context(request)
    context.update({
        "period": period,
        "period_label": period_label,
        "periods": PERIODS,
        "since": since,
        "now": now,
        "coverage_start": coverage_start,
        "ingestion": summarize(runs.filter(kind=OperationalRun.Kind.INGESTION)),
        "analysis": summarize(runs.filter(kind=OperationalRun.Kind.ANALYSIS)),
        "ai_call_stages": ai_call_stages,
        "recovery": summarize(runs.filter(kind=OperationalRun.Kind.RECOVERY)),
        "superseded_analyses": VacancyAnalysis.objects.filter(
            status=VacancyAnalysis.Status.SUPERSEDED,
            updated_at__gte=since,
            updated_at__lte=now,
        ).count(),
        "source_rows": source_rows,
        "pending_count": pending.count(),
        "oldest_pending": oldest_pending,
        "oldest_pending_age": now - oldest_pending if oldest_pending else None,
        "latest_errors": latest_errors,
        "admin_commands": AdminCommandRun.objects.select_related("requested_by").all()[:20],
        "allowed_commands": ALLOWED_COMMANDS,
    })
    return render(request, "operations/dashboard.html", context)
