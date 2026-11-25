from pathlib import Path
import hashlib
import json
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from .forms import ProfileForm
from .models import GuidedTourProgress, Profile, ProfileRevision
from .tour import TOUR_STEPS, TOUR_VERSION, ensure_mandatory_tour, is_tour_eligible, step_payload
from dashboard.score_display import score_star_label, score_star_percent, score_star_threshold_label
from dashboard.models import PushSubscription, RecommendationEvent


def _push_endpoint_digest(endpoint):
    return hashlib.sha256(endpoint.encode("utf-8")).hexdigest()


def _valid_push_endpoint(endpoint):
    endpoint = str(endpoint or "").strip()
    parsed = urlparse(endpoint)
    if len(endpoint) > 4096 or parsed.scheme != "https" or not parsed.netloc:
        return ""
    return endpoint


def _push_request_data(request):
    if len(request.body) > 8192:
        return None
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(owner=request.user)
    if request.method == "POST":
        # ModelForms bind and mutate `profile` during validation. Keep a
        # snapshot so comparisons reflect persisted values, not form values.
        original_profile_values = {
            "search_phrases": list(profile.search_phrases or []),
            "locations": list(profile.locations or []),
            "remote_ok": profile.remote_ok,
        }
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Compare the normalized values. The chip editor submits JSON while
            # the form's initial values are newline-delimited, so changed_data
            # can incorrectly treat an unchanged profile as a new revision.
            profile_fields_changed = any((
                form.cleaned_data.get("search_phrases", original_profile_values["search_phrases"]) != original_profile_values["search_phrases"],
                form.cleaned_data.get("locations", original_profile_values["locations"]) != original_profile_values["locations"],
                form.cleaned_data.get("remote_ok", original_profile_values["remote_ok"]) != original_profile_values["remote_ok"],
                bool(request.FILES.get(form.add_prefix("cv_file"))),
            ))
            with transaction.atomic():
                profile = form.save(commit=False)
                if profile_fields_changed:
                    profile.revision_number += 1
                profile.save()
                if profile_fields_changed:
                    ProfileRevision.objects.create(
                        profile=profile,
                        version=profile.revision_number,
                        search_phrases=profile.search_phrases,
                        locations=profile.locations,
                        remote_ok=profile.remote_ok,
                        cv_file_path=profile.cv_file.name if profile.cv_file else "",
                    )
                    from matching.tasks import schedule_profile_analyses
                    from jobs.tasks import refresh_profile_sources

                    transaction.on_commit(lambda profile_id=profile.pk: schedule_profile_analyses.delay(profile_id))
                    transaction.on_commit(lambda profile_id=profile.pk: refresh_profile_sources.delay(profile_id))
            messages.success(request, "Tu perfil quedó actualizado.")
            return redirect("profiles:edit")
    else:
        form = ProfileForm(instance=profile)
    try:
        min_score_value = int(form["min_score"].value() or 0) if form.is_bound else (profile.min_score_stars or 0) * 2
    except (TypeError, ValueError):
        min_score_value = (profile.min_score_stars or 0) * 2
    score_values = list(range(0, 11, 2))
    min_score_options = []
    for score_value in sorted(score_values):
        threshold_label = score_star_threshold_label(score_value)
        min_score_options.append({
            "value": score_value,
            "percent": score_star_percent(score_value),
            "label": "Sin descarte" if score_value == 0 else threshold_label,
            "aria_label": (
                "No descartar vacantes por puntaje"
                if score_value == 0
                else f"Descartar automáticamente vacantes nuevas con menos de {score_value // 2} estrellas"
            ),
            "selected": score_value == min_score_value,
        })
    return render(request, "profiles/edit.html", {
        "form": form,
        "profile": profile,
        "min_score_value": min_score_value,
        "min_score_star_label": score_star_label(min_score_value),
        "min_score_star_threshold_label": score_star_threshold_label(min_score_value),
        "min_score_star_percent": min_score_value * 10,
        "min_score_options": min_score_options,
        "push_vapid_public_key": settings.PUSH_VAPID_PUBLIC_KEY,
        "push_enabled_for_environment": bool(
            settings.PUSH_VAPID_PUBLIC_KEY
            and settings.PUSH_VAPID_PRIVATE_KEY
            and settings.PUSH_VAPID_SUBJECT
        ),
    })


@login_required
@require_POST
def push_subscription_status(request):
    payload = _push_request_data(request)
    endpoint = _valid_push_endpoint(payload.get("endpoint") if payload else "")
    profile = Profile.objects.filter(owner=request.user).first()
    if not endpoint or not profile:
        return JsonResponse({"active": False}, status=400)
    active = PushSubscription.objects.filter(
        profile=profile,
        endpoint_digest=_push_endpoint_digest(endpoint),
        active=True,
    ).exists()
    return JsonResponse({"active": active})


@login_required
@require_POST
@transaction.atomic
def save_push_subscription(request):
    payload = _push_request_data(request)
    action = payload.get("action") if payload else None
    if action == "unsubscribe":
        endpoint = _valid_push_endpoint(payload.get("endpoint"))
        profile = Profile.objects.filter(owner=request.user).first()
        if not endpoint or not profile:
            return JsonResponse({"active": False}, status=400)
        PushSubscription.objects.filter(
            profile=profile,
            endpoint_digest=_push_endpoint_digest(endpoint),
        ).delete()
        return JsonResponse({"active": False})

    subscription = payload.get("subscription") if payload else None
    endpoint = _valid_push_endpoint(
        subscription.get("endpoint") if isinstance(subscription, dict) else ""
    )
    keys = subscription.get("keys") if isinstance(subscription, dict) else None
    p256dh = str((keys or {}).get("p256dh") or "").strip() if isinstance(keys, dict) else ""
    auth_key = str((keys or {}).get("auth") or "").strip() if isinstance(keys, dict) else ""
    profile = Profile.objects.filter(owner=request.user).first()
    if (
        not endpoint or not p256dh or not auth_key
        or len(p256dh) > 256 or len(auth_key) > 128 or not profile
    ):
        return JsonResponse(
            {"active": False, "message": "La suscripción del navegador no es válida."},
            status=400,
        )
    digest = _push_endpoint_digest(endpoint)
    latest_event_id = (
        RecommendationEvent.objects.filter(profile=profile).aggregate(max_id=Max("pk"))["max_id"]
        or 0
    )
    row = PushSubscription.objects.select_for_update().filter(endpoint_digest=digest).first()
    if row is None:
        row = PushSubscription.objects.create(
            profile=profile,
            endpoint_digest=digest,
            endpoint=endpoint,
            p256dh_key=p256dh,
            auth_key=auth_key,
            active=True,
            activated_at=timezone.now(),
            last_event_cutoff_id=latest_event_id,
        )
    else:
        changed_account = row.profile_id != profile.pk
        row.profile = profile
        row.endpoint = endpoint
        row.p256dh_key = p256dh
        row.auth_key = auth_key
        row.active = True
        update_fields = [
            "profile", "endpoint_ciphertext", "p256dh_ciphertext", "auth_ciphertext",
            "active", "updated_at",
        ]
        if changed_account:
            row.activated_at = timezone.now()
            row.last_event_cutoff_id = latest_event_id
            update_fields.extend(["activated_at", "last_event_cutoff_id"])
        row.save(update_fields=update_fields)
    return JsonResponse({"active": True})


@login_required
@require_POST
def logout_with_push_unlink(request):
    endpoint = _valid_push_endpoint(request.POST.get("push_endpoint"))
    if endpoint:
        profile = Profile.objects.filter(owner=request.user).first()
        if profile:
            PushSubscription.objects.filter(
                profile=profile,
                endpoint_digest=_push_endpoint_digest(endpoint),
            ).delete()
    logout(request)
    return redirect("login")


@require_GET
def push_service_worker(_request):
    response = HttpResponse(
        """self.addEventListener('push', (event) => {
  event.waitUntil(self.registration.showNotification('Novedades en Ramper Job', {
    body: 'Hay recomendaciones nuevas. Abre Ramper Job para revisarlas.',
    silent: true,
    data: { url: '/' }
  }));
});
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const destination = new URL('/', self.location.origin).href;
  event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windows) => {
    for (const client of windows) {
      if (new URL(client.url).origin === self.location.origin) {
        return client.focus().then(() => client.navigate(destination));
      }
    }
    return clients.openWindow(destination);
  }));
});
""",
        content_type="application/javascript; charset=utf-8",
    )
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-store"
    return response


@login_required
@require_GET
def download_cv(request):
    profile = Profile.objects.filter(owner=request.user).first()
    if not profile or not profile.cv_file:
        raise Http404
    try:
        file_handle = profile.cv_file.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    return FileResponse(file_handle, as_attachment=True, filename=Path(profile.cv_file.name).name)


@login_required
@require_GET
def download_private_cv(request, file_path):
    profile = Profile.objects.filter(owner=request.user, cv_file=file_path).first()
    if not profile:
        raise Http404
    return download_cv(request)


def _guided_tour_state(progress):
    if progress is None or progress.version != TOUR_VERSION:
        return {
            "status": GuidedTourProgress.Status.NOT_STARTED,
            "version": TOUR_VERSION,
            "mandatory": progress is None or not progress.mandatory_completed,
            "offer": progress is not None and progress.mandatory_completed,
            "step": None,
            "step_index": 0,
            "step_count": len(TOUR_STEPS),
        }

    step_ids = [step["id"] for step in TOUR_STEPS]
    current_step = progress.current_step
    if current_step not in step_ids:
        current_step = step_ids[0]
    step_index = step_ids.index(current_step)
    return {
        "status": progress.status,
        "version": progress.version,
        "mandatory": not progress.mandatory_completed,
        "offer": progress.mandatory_completed and progress.status == GuidedTourProgress.Status.NOT_STARTED,
        "step": step_payload(current_step) if progress.status == GuidedTourProgress.Status.IN_PROGRESS else None,
        "step_index": step_index + 1,
        "step_count": len(TOUR_STEPS),
    }


@login_required
@require_GET
def guided_tour_state(request):
    if not is_tour_eligible(request.user):
        raise Http404
    progress = ensure_mandatory_tour(request.user)
    if progress is None:
        progress = GuidedTourProgress.objects.filter(owner=request.user).first()
    return JsonResponse(_guided_tour_state(progress))


@login_required
@require_POST
def guided_tour_action(request):
    if not is_tour_eligible(request.user):
        raise Http404

    action = request.POST.get("action", "")
    allowed_actions = {"start", "reopen", "next", "previous", "skip", "close"}
    if action not in allowed_actions:
        return JsonResponse({"error": "Acción no válida."}, status=400)

    progress = GuidedTourProgress.objects.filter(owner=request.user).first()
    mandatory = progress is None or not progress.mandatory_completed
    if mandatory:
        progress = ensure_mandatory_tour(request.user)
        if action in {"skip", "close"}:
            return JsonResponse({"error": "Debes completar el recorrido para continuar."}, status=409)
    step_ids = [step["id"] for step in TOUR_STEPS]
    first_step, last_step = step_ids[0], step_ids[-1]

    if action in {"start", "reopen"}:
        progress, _created = GuidedTourProgress.objects.get_or_create(owner=request.user)
        if progress.mandatory_completed:
            progress.version = TOUR_VERSION
            progress.status = GuidedTourProgress.Status.IN_PROGRESS
            progress.current_step = first_step
    elif action == "skip":
        if progress is None:
            progress = GuidedTourProgress(owner=request.user)
        progress.version = TOUR_VERSION
        progress.status = GuidedTourProgress.Status.SKIPPED
        if progress.current_step not in step_ids:
            progress.current_step = first_step
    else:
        if (
            progress is None
            or progress.version != TOUR_VERSION
            or progress.status != GuidedTourProgress.Status.IN_PROGRESS
        ):
            return JsonResponse({"error": "No hay un recorrido en curso."}, status=409)
        current_step = progress.current_step if progress.current_step in step_ids else first_step
        step_index = step_ids.index(current_step)
        if action == "next":
            if step_index == len(step_ids) - 1:
                progress.current_step = last_step
                progress.status = GuidedTourProgress.Status.COMPLETED
                progress.mandatory_completed = True
            else:
                progress.current_step = step_ids[step_index + 1]
        elif action == "previous":
            progress.current_step = step_ids[max(0, step_index - 1)]
        elif action == "close":
            progress.current_step = current_step

    progress.save()
    return JsonResponse(_guided_tour_state(progress))
