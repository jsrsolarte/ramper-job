from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ProfileForm
from .models import GuidedTourProgress, Profile, ProfileRevision
from .tour import TOUR_STEPS, TOUR_VERSION, is_tour_eligible, step_payload
from dashboard.score_display import score_star_label, score_star_percent, score_star_threshold_label


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
        min_score_value = int(form["min_score"].value() or 0)
    except (TypeError, ValueError):
        min_score_value = profile.min_score or 0
    score_values = list(range(0, 11, 2))
    if 0 <= min_score_value <= 10 and min_score_value not in score_values:
        score_values.append(min_score_value)
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
                else f"Descartar automáticamente vacantes nuevas con menos de {score_value} de 10 puntos, {threshold_label}"
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
    })


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
            "offer": True,
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
        "offer": progress.status == GuidedTourProgress.Status.NOT_STARTED,
        "step": step_payload(current_step) if progress.status == GuidedTourProgress.Status.IN_PROGRESS else None,
        "step_index": step_index + 1,
        "step_count": len(TOUR_STEPS),
    }


@login_required
@require_GET
def guided_tour_state(request):
    if not is_tour_eligible(request.user):
        raise Http404
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
    step_ids = [step["id"] for step in TOUR_STEPS]
    first_step, last_step = step_ids[0], step_ids[-1]

    if action in {"start", "reopen"}:
        progress, _created = GuidedTourProgress.objects.get_or_create(owner=request.user)
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
            else:
                progress.current_step = step_ids[step_index + 1]
        elif action == "previous":
            progress.current_step = step_ids[max(0, step_index - 1)]
        elif action == "close":
            progress.current_step = current_step

    progress.save()
    return JsonResponse(_guided_tour_state(progress))
