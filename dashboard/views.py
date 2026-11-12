from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Max, OuterRef, Subquery
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.models import VacancyFollowUp
from dashboard.score_distribution import build_score_summary
from dashboard.score_display import score_star_label, score_star_percent, score_star_threshold_label
from dashboard.services import discard_follow_up
from dashboard.time_format import publication_age, relative_age
from jobs.models import JobSourceStatus
from matching.models import AICallAttempt, RUBRIC_CRITERIA, RUBRIC_VERSION, VacancyAnalysis
from profiles.models import Profile
from profiles.locations import vacancy_location_is_eligible
from operations.scheduling import next_periodic_refresh_schedule


def _current_score_analyses(profile):
    if not profile:
        return [], None, set()

    revision = profile.revisions.filter(version=profile.revision_number).first()
    latest_result = VacancyAnalysis.objects.filter(
        profile=OuterRef("profile"),
        vacancy=OuterRef("vacancy"),
        status=VacancyAnalysis.Status.COMPLETED,
        profile_revision__version=F("profile__revision_number"),
        matching_config__rubric_version=RUBRIC_VERSION,
    ).order_by("-created_at", "-pk").values("pk")[:1]
    analyses = list(
        VacancyAnalysis.objects.filter(
            profile=profile,
            status=VacancyAnalysis.Status.COMPLETED,
            profile_revision__version=profile.revision_number,
            matching_config__rubric_version=RUBRIC_VERSION,
            score__gte=0,
            score__lte=10,
        )
        .exclude(score_breakdown={})
        .annotate(latest_result_id=Subquery(latest_result))
        .filter(pk=F("latest_result_id"))
        .select_related("vacancy", "organization")
        .order_by("-score", "-created_at")
    )
    archived_vacancy_ids = set(
        VacancyFollowUp.objects.filter(profile=profile, archived_at__isnull=False)
        .values_list("vacancy_id", flat=True)
    )
    if revision:
        analyses = [
            analysis for analysis in analyses
            if analysis.vacancy_id not in archived_vacancy_ids
            and vacancy_location_is_eligible(analysis.vacancy, revision)
        ]
    return analyses, revision, archived_vacancy_ids


@login_required
def home(request):
    profile = Profile.objects.filter(owner=request.user).first()
    if profile:
        profile.min_score_star_threshold_label = score_star_threshold_label(profile.min_score)
    analyses = VacancyAnalysis.objects.none()
    score_summary = build_score_summary([])
    score_filter = None
    follow_up_counts = {status: 0 for status, _label in VacancyFollowUp.Status.choices}
    follow_up_status = request.GET.get("state", VacancyFollowUp.Status.PENDING)
    if follow_up_status not in VacancyFollowUp.Status.values:
        follow_up_status = VacancyFollowUp.Status.PENDING
    state_names = {
        VacancyFollowUp.Status.PENDING: "recomendadas",
        VacancyFollowUp.Status.DISCARDED: "descartadas",
        VacancyFollowUp.Status.APPLIED: "aplicadas",
        VacancyFollowUp.Status.IN_PROGRESS: "en proceso",
        VacancyFollowUp.Status.INTERVIEW: "en entrevista",
        VacancyFollowUp.Status.FINALIZED: "finalizadas",
    }
    if profile:
        requested_score_filter = request.GET.get("score_min", "")
        try:
            requested_score_filter = int(requested_score_filter)
        except (TypeError, ValueError):
            requested_score_filter = None
        if requested_score_filter is not None and 0 <= requested_score_filter <= 10:
            score_filter = requested_score_filter
        if follow_up_status != VacancyFollowUp.Status.PENDING:
            score_filter = None
        score_filter_value = score_filter if score_filter is not None else 0
        score_filter_options = []
        if follow_up_status == VacancyFollowUp.Status.PENDING:
            thresholds = list(range(0, 11, 2))
            for threshold in thresholds:
                label = score_star_threshold_label(threshold)
                score_filter_options.append({
                    "value": threshold,
                    "label": "Todas" if threshold == 0 else label,
                    "percent": score_star_percent(threshold),
                    "selected": threshold == score_filter_value,
                })
        effective_min_score = score_filter_value if follow_up_status == VacancyFollowUp.Status.PENDING else 0
        analyses, revision, archived_vacancy_ids = _current_score_analyses(profile)
        follow_up_rows = VacancyFollowUp.objects.filter(profile=profile)
        score_summary = build_score_summary(
            (analysis.score for analysis in analyses),
            minimum_score=profile.min_score,
        )
        suggested_score = score_summary["suggested_score"]
        if (
            follow_up_status == VacancyFollowUp.Status.PENDING
            and suggested_score is not None
            and all(option["value"] != suggested_score for option in score_filter_options)
        ):
            score_filter_options.append({
                "value": suggested_score,
                "label": score_star_threshold_label(suggested_score),
                "percent": score_star_percent(suggested_score),
                "selected": suggested_score == score_filter_value,
            })
            score_filter_options.sort(key=lambda option: option["value"])
        follow_ups = {
            follow_up.vacancy_id: follow_up
            for follow_up in follow_up_rows.filter(
                vacancy_id__in=[analysis.vacancy_id for analysis in analyses],
                archived_at__isnull=True,
            )
        }
        now = timezone.now()
        for analysis in analyses:
            follow_up = follow_ups.get(analysis.vacancy_id)
            analysis.follow_up_status = follow_up.status if follow_up else VacancyFollowUp.Status.PENDING
            analysis.follow_up_state_changed_at = (
                follow_up.state_changed_at if follow_up else analysis.completed_at
            )
            analysis.follow_up_label = dict(VacancyFollowUp.Status.choices)[analysis.follow_up_status]
            analysis.published_age, analysis.publication_absolute = publication_age(
                analysis.vacancy.published_at, analysis.vacancy.raw_data, now=now
            )
            analysis.analyzed_age = relative_age(analysis.completed_at, now=now)
            if follow_up and follow_up.state_changed_at:
                state_prefix = {
                    VacancyFollowUp.Status.PENDING: "Recomendación",
                    VacancyFollowUp.Status.DISCARDED: "Descartada",
                    VacancyFollowUp.Status.APPLIED: "Aplicada",
                    VacancyFollowUp.Status.IN_PROGRESS: "En proceso",
                    VacancyFollowUp.Status.INTERVIEW: "Entrevista",
                    VacancyFollowUp.Status.FINALIZED: "Finalizada",
                }[follow_up.status]
                analysis.state_age = relative_age(follow_up.state_changed_at, now=now)
                analysis.state_age_prefix = state_prefix
                analysis.state_changed_at = follow_up.state_changed_at
            follow_up_counts[analysis.follow_up_status] += 1
            next_statuses = {
                VacancyFollowUp.Status.PENDING: [(VacancyFollowUp.Status.APPLIED, "Marcar como aplicada")],
                VacancyFollowUp.Status.APPLIED: [
                    (VacancyFollowUp.Status.IN_PROGRESS, "Mover a en proceso"),
                    (VacancyFollowUp.Status.FINALIZED, "Finalizar proceso"),
                ],
                VacancyFollowUp.Status.IN_PROGRESS: [
                    (VacancyFollowUp.Status.INTERVIEW, "Mover a entrevista"),
                    (VacancyFollowUp.Status.FINALIZED, "Finalizar proceso"),
                ],
                VacancyFollowUp.Status.INTERVIEW: [
                    (VacancyFollowUp.Status.FINALIZED, "Finalizar proceso")
                ],
                VacancyFollowUp.Status.FINALIZED: [],
                VacancyFollowUp.Status.DISCARDED: [],
            }
            analysis.follow_up_actions = next_statuses[analysis.follow_up_status]
            analysis.can_discard = analysis.follow_up_status != VacancyFollowUp.Status.DISCARDED
        analyses = [
            analysis for analysis in analyses
            if analysis.follow_up_status == follow_up_status
            and (follow_up_status != VacancyFollowUp.Status.PENDING or analysis.score >= effective_min_score)
        ]
        if follow_up_status == VacancyFollowUp.Status.PENDING:
            analyses.sort(key=lambda analysis: (analysis.score, analysis.created_at, analysis.pk), reverse=True)
        else:
            analyses.sort(
                key=lambda analysis: (
                    analysis.follow_up_state_changed_at.timestamp()
                    if analysis.follow_up_state_changed_at else 0,
                    analysis.vacancy_id,
                    analysis.pk,
                ),
                reverse=True,
            )
        for analysis in analyses:
            vacancy = analysis.vacancy
            analysis.score_star_percent = score_star_percent(analysis.score)
            analysis.score_star_label = score_star_label(analysis.score)
            details = (vacancy.raw_data or {}).get("details") or {}

            def clean(value):
                value = str(value or "").strip()
                if value.casefold().rstrip(".") in {"cop", "n/a", "no informado"}:
                    return ""
                if value.upper() in {
                    "CONTRACTOR", "FULL_TIME", "INTERNSHIP", "OTHER", "PART_TIME",
                    "PER_DIEM", "TEMPORARY", "UNKNOWN", "VOLUNTEER",
                }:
                    return ""
                return {
                    "PERMANENT": "Indefinido",
                    "MONTH": "Mensual",
                    "YEAR": "Anual",
                    "WEEK": "Semanal",
                    "DAY": "Diario",
                }.get(value.upper(), value)

            salary = clean(vacancy.salary) or clean(details.get("salary_text")) or clean(details.get("list_salary"))
            city = clean(details.get("city"))
            address = clean(details.get("address"))
            if city and address and city.casefold().strip(" .") == address.casefold().strip(" ."):
                address = ""
            location = " · ".join(filter(None, (city, address)))
            analysis.vacancy_facts = [
                ("Ubicación", location or clean(vacancy.location) or "No informada"),
                ("Salario", salary or "No informado"),
                ("Tipo de contrato", clean(vacancy.contract_type) or clean(details.get("contract_type")) or "No informado"),
                ("Modalidad", clean(details.get("modality")) or "No informada"),
            ]
            for label, key in (
                ("Rango publicado", "list_salary"),
                ("Periodicidad", "salary_periodicity"),
                ("Área", "area"),
                ("Nivel educativo", "education"),
                ("Experiencia", "experience"),
                ("Horario", "schedule"),
                ("Vacantes", "vacancy_count"),
            ):
                value = clean(details.get(key))
                if value:
                    analysis.vacancy_facts.append((label, value))
            organized_content = dict(
                analysis.organization.content if analysis.organization_id and analysis.organization else {}
            )
            summary = clean(organized_content.get("summary"))
            analysis.dashboard_organized_content = {
                **organized_content,
                "summary": summary,
                **{
                    key: [value for value in (clean(item) for item in organized_content.get(key, [])) if value]
                    for key in ("keywords", "responsibilities", "requirements", "conditions")
                },
            }
            analysis.organization_status_label = dict(VacancyAnalysis.OrganizationStatus.choices).get(
                analysis.organization_status, "Pendiente"
            )
            status_labels = {
                "cumple": "Cumple",
                "parcial": "Parcial",
                "sin_evidencia": "Sin evidencia",
                "contradicho": "Contradicho",
                "no_aplica": "No aplica",
            }
            breakdown = analysis.score_breakdown or {}
            analysis.rubric_details = [
                {
                    "label": definition["label"],
                    "score": breakdown.get(key, {}).get("score", 0),
                    "max_score": definition["max_score"],
                    "status": status_labels.get(breakdown.get(key, {}).get("status"), "Sin información"),
                    "evidence": breakdown.get(key, {}).get("evidence", ""),
                }
                for key, definition in RUBRIC_CRITERIA.items()
            ]
            analysis.critical_requirements = breakdown.get("critical_requirements", [])
            analysis.score_deductions = breakdown.get("deductions", [])
    pending_count = 0
    if profile:
        current_revision = profile.revisions.filter(version=profile.revision_number).first()
        latest_analysis = VacancyAnalysis.objects.filter(
            profile=OuterRef("profile"), profile_revision=OuterRef("profile_revision"),
            vacancy=OuterRef("vacancy"), matching_config__rubric_version=RUBRIC_VERSION,
        ).order_by("-created_at", "-pk").values("pk")[:1]
        pending = VacancyAnalysis.objects.filter(
            profile=profile, status__in=[VacancyAnalysis.Status.PENDING, VacancyAnalysis.Status.FAILED],
            matching_config__rubric_version=RUBRIC_VERSION,
        ).annotate(latest_id=Subquery(latest_analysis)).filter(pk=F("latest_id")).select_related("vacancy", "profile_revision")
        if current_revision:
            pending_count = len({
                analysis.vacancy_id
                for analysis in pending
                if analysis.profile_revision_id == current_revision.pk
                and vacancy_location_is_eligible(analysis.vacancy, current_revision)
            })
    page = Paginator(analyses, 20).get_page(request.GET.get("page"))
    page_query = request.GET.copy()
    page_query.pop("page", None)
    page_navigation = []
    previous_page_query = next_page_query = ""
    if page.has_other_pages():
        if page.has_previous():
            previous_query = page_query.copy()
            previous_query["page"] = page.previous_page_number()
            previous_page_query = previous_query.urlencode()
        if page.has_next():
            next_query = page_query.copy()
            next_query["page"] = page.next_page_number()
            next_page_query = next_query.urlencode()
        for item in page.paginator.get_elided_page_range(
            number=page.number, on_each_side=1, on_ends=1
        ):
            if item == page.paginator.ELLIPSIS:
                page_navigation.append({"ellipsis": True})
                continue
            query = page_query.copy()
            query["page"] = item
            page_navigation.append({
                "number": item,
                "current": item == page.number,
                "querystring": query.urlencode(),
            })
    unavailable_sources = JobSourceStatus.objects.filter(available=False).exclude(status_message="")
    return render(
        request,
        "dashboard/home.html",
        {
            "profile": profile,
            "automatic_refresh_schedule": next_periodic_refresh_schedule(),
            "analyses": page,
            "page_navigation": page_navigation,
            "previous_page_query": previous_page_query,
            "next_page_query": next_page_query,
            "pending_count": pending_count,
            "score_distribution": score_summary["bands"],
            "score_distribution_sample_size": score_summary["sample_size"],
            "score_distribution_maximum_count": score_summary["maximum_count"],
            "score_recommended_min": score_summary["suggested_score"],
            "score_recommended_count": score_summary["suggested_count"],
            "score_recommendation_below_profile": score_summary["suggestion_below_profile"],
            "unavailable_sources": unavailable_sources,
        "score_filter": score_filter,
        "score_filter_value": score_filter if score_filter is not None else 0,
        "score_filter_options": score_filter_options if profile else [],
            "score_filter_star_percent": (score_filter if score_filter is not None else 0) * 10,
            "score_filter_star_label": score_star_threshold_label(
                score_filter if score_filter is not None else 0
            ),
            "follow_up_choices": VacancyFollowUp.Status.choices,
            "follow_up_status": follow_up_status,
            "active_tab": (
                "recommendations"
                if follow_up_status == VacancyFollowUp.Status.PENDING
                else follow_up_status
            ),
            "follow_up_counts": follow_up_counts,
            "follow_up_empty_title": f"No hay vacantes {state_names[follow_up_status]}",
        },
    )


@login_required
def analysis(request):
    profile = Profile.objects.filter(owner=request.user).first()
    if profile:
        profile.min_score_star_threshold_label = score_star_threshold_label(profile.min_score)
    score_analyses, _revision, _archived_vacancy_ids = _current_score_analyses(profile)
    score_summary = build_score_summary(
        (analysis.score for analysis in score_analyses),
        minimum_score=profile.min_score if profile else 0,
    )
    return render(
        request,
        "dashboard/analysis.html",
        {
            "profile": profile,
            "active_tab": "analysis",
            "score_distribution": score_summary["bands"],
            "score_distribution_sample_size": score_summary["sample_size"],
            "score_recommended_min": score_summary["suggested_score"],
            "score_recommended_count": score_summary["suggested_count"],
            "score_recommendation_below_profile": score_summary["suggestion_below_profile"],
        },
    )


@login_required
def pending(request):
    profile = Profile.objects.filter(owner=request.user).first()
    analyses = []
    follow_up_counts = {status: 0 for status, _label in VacancyFollowUp.Status.choices}
    if profile:
        revision = profile.revisions.filter(version=profile.revision_number).first()
        if revision:
            latest_result = VacancyAnalysis.objects.filter(
                profile=OuterRef("profile"),
                vacancy=OuterRef("vacancy"),
                status=VacancyAnalysis.Status.COMPLETED,
                profile_revision__version=F("profile__revision_number"),
                matching_config__rubric_version=RUBRIC_VERSION,
            ).order_by("-created_at", "-pk").values("pk")[:1]
            completed = VacancyAnalysis.objects.filter(
                profile=profile,
                status=VacancyAnalysis.Status.COMPLETED,
                profile_revision=revision,
                matching_config__rubric_version=RUBRIC_VERSION,
                score__lte=10,
            ).exclude(score_breakdown={}).annotate(latest_result_id=Subquery(latest_result))
            completed = completed.filter(pk=F("latest_result_id")).select_related("vacancy")
            follow_up_statuses = {
                follow_up.vacancy_id: follow_up.status
                for follow_up in VacancyFollowUp.objects.filter(
                    profile=profile,
                    vacancy_id__in=completed.values("vacancy_id"),
                    archived_at__isnull=True,
                )
            }
            archived_vacancy_ids = set(VacancyFollowUp.objects.filter(
                profile=profile,
                vacancy_id__in=completed.values("vacancy_id"),
                archived_at__isnull=False,
            ).values_list("vacancy_id", flat=True))
            for analysis in completed:
                if (
                    analysis.vacancy_id not in archived_vacancy_ids
                    and vacancy_location_is_eligible(analysis.vacancy, revision)
                ):
                    status = follow_up_statuses.get(analysis.vacancy_id, VacancyFollowUp.Status.PENDING)
                    follow_up_counts[status] += 1
            latest_pending = VacancyAnalysis.objects.filter(
                profile=OuterRef("profile"),
                profile_revision=OuterRef("profile_revision"),
                vacancy=OuterRef("vacancy"),
                matching_config__rubric_version=RUBRIC_VERSION,
            ).order_by("-created_at", "-pk").values("pk")[:1]
            candidates = VacancyAnalysis.objects.filter(
                profile=profile,
                profile_revision=revision,
                status__in=[VacancyAnalysis.Status.PENDING, VacancyAnalysis.Status.FAILED],
                matching_config__rubric_version=RUBRIC_VERSION,
            ).annotate(latest_pending_id=Subquery(latest_pending))
            candidates = candidates.filter(pk=F("latest_pending_id")).select_related("vacancy")
            analyses = [
                analysis
                for analysis in candidates.order_by("-created_at", "-pk")
                if vacancy_location_is_eligible(analysis.vacancy, revision)
            ]
            failed_attempts = {
                row["analysis__vacancy_id"]: row["count"]
                for row in AICallAttempt.objects.filter(
                    analysis__profile=profile,
                    analysis__vacancy_id__in=[item.vacancy_id for item in analyses],
                    stage=AICallAttempt.Stage.SCORING,
                    outcome__in=[AICallAttempt.Outcome.FAILED, AICallAttempt.Outcome.RETRYING],
                ).values("analysis__vacancy_id").annotate(count=Count("pk"))
            }
            latest_attempts = {
                row["analysis_id"]: row["last_attempt_at"]
                for row in AICallAttempt.objects.filter(
                    analysis_id__in=[item.pk for item in analyses],
                    stage=AICallAttempt.Stage.SCORING,
                ).values("analysis_id").annotate(last_attempt_at=Max("created_at"))
            }
            for analysis in analyses:
                analysis.failed_attempt_count = failed_attempts.get(analysis.vacancy_id, 0)
                analysis.last_attempt_at = latest_attempts.get(analysis.pk)
                vacancy = analysis.vacancy
                details = (vacancy.raw_data or {}).get("details") or {}
                analysis.pending_fields = [
                    (label, value)
                    for label, value in (
                        ("Ubicación", vacancy.location or details.get("city")),
                        ("Salario", vacancy.salary or details.get("salary_text") or details.get("list_salary")),
                        ("Tipo de contrato", vacancy.contract_type or details.get("contract_type")),
                    )
                    if value and str(value).strip()
                ]
    return render(
        request,
        "dashboard/pending.html",
        {
            "profile": profile,
            "pending_analyses": analyses,
            "pending_count": len(analyses),
            "follow_up_counts": follow_up_counts,
            "active_tab": "pending",
        },
    )


@login_required
@require_POST
@transaction.atomic
def update_follow_up(request, vacancy_id):
    profile = Profile.objects.select_for_update().filter(owner=request.user).first()
    if not profile:
        return HttpResponseBadRequest("No hay un perfil asociado a esta cuenta.")

    status = request.POST.get("status", "")
    if status not in VacancyFollowUp.Status.values and status != "restore":
        return HttpResponseBadRequest("El estado de seguimiento no es válido.")

    revision = profile.revisions.filter(version=profile.revision_number).first()
    analysis = get_object_or_404(
        VacancyAnalysis.objects.filter(
            profile=profile,
            status=VacancyAnalysis.Status.COMPLETED,
            profile_revision__version=profile.revision_number,
            matching_config__rubric_version=RUBRIC_VERSION,
            score__lte=10,
        )
        .exclude(score_breakdown={})
        .filter(
            pk=Subquery(
                VacancyAnalysis.objects.filter(
                    profile=OuterRef("profile"),
                    vacancy=OuterRef("vacancy"),
                    status=VacancyAnalysis.Status.COMPLETED,
                    profile_revision__version=F("profile__revision_number"),
                    matching_config__rubric_version=RUBRIC_VERSION,
                ).order_by("-created_at", "-pk").values("pk")[:1]
            )
        )
        .select_related("vacancy"),
        vacancy_id=vacancy_id,
    )
    if revision and not vacancy_location_is_eligible(analysis.vacancy, revision):
        return HttpResponseBadRequest("La vacante no está disponible para este perfil.")

    follow_up = VacancyFollowUp.objects.filter(profile=profile, vacancy=analysis.vacancy).first()
    current_status = follow_up.status if follow_up else VacancyFollowUp.Status.PENDING
    if status == VacancyFollowUp.Status.DISCARDED:
        follow_up, _changed = discard_follow_up(profile, analysis.vacancy)
        target_status = VacancyFollowUp.Status.DISCARDED
    elif status == "restore":
        if follow_up is None or current_status != VacancyFollowUp.Status.DISCARDED:
            return HttpResponseBadRequest("Solo se pueden restaurar vacantes descartadas.")
        target_status = follow_up.previous_status
        if target_status not in VacancyFollowUp.Status.values or target_status == VacancyFollowUp.Status.DISCARDED:
            target_status = VacancyFollowUp.Status.PENDING
        follow_up.status = target_status
        follow_up.state_changed_at = timezone.now()
        follow_up.save(update_fields=["status", "state_changed_at", "updated_at"])
    else:
        allowed_next_statuses = {
            VacancyFollowUp.Status.PENDING: {VacancyFollowUp.Status.APPLIED},
            VacancyFollowUp.Status.APPLIED: {
                VacancyFollowUp.Status.IN_PROGRESS,
                VacancyFollowUp.Status.FINALIZED,
            },
            VacancyFollowUp.Status.IN_PROGRESS: {
                VacancyFollowUp.Status.INTERVIEW,
                VacancyFollowUp.Status.FINALIZED,
            },
            VacancyFollowUp.Status.INTERVIEW: {VacancyFollowUp.Status.FINALIZED},
            VacancyFollowUp.Status.FINALIZED: set(),
            VacancyFollowUp.Status.DISCARDED: set(),
        }
        if status != current_status and status not in allowed_next_statuses[current_status]:
            return HttpResponseBadRequest("La vacante solo puede avanzar a la siguiente etapa permitida.")
        target_status = current_status if status == current_status else status
        if follow_up is None:
            follow_up = VacancyFollowUp.objects.create(
                profile=profile,
                vacancy=analysis.vacancy,
                status=target_status,
            )
        elif target_status != current_status:
            follow_up.status = target_status
            follow_up.state_changed_at = timezone.now()
            follow_up.save(update_fields=["status", "state_changed_at", "updated_at"])
    messages.success(request, "Se actualizó el seguimiento de la vacante.")
    return redirect(f"/?state={target_status}")
