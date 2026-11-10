import logging
import hashlib
import json
from time import perf_counter
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import Exists, F, OuterRef, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from jobs.models import Vacancy
from matching.client import OmniRouteError, request_model_analysis, request_model_organization
from matching.models import AICallAttempt, PROMPT_VERSION, RUBRIC_VERSION, MatchingConfig, ProfileVacancyDiscovery, VacancyAnalysis, VacancyOrganization
from matching.schemas import InvalidAnalysisError, save_validated_analysis, save_validated_organization
from matching.services import RUBRIC_PROMPT, get_active_matching_config
from profiles.extract import extract_revision_text
from profiles.models import Profile
from profiles.locations import expand_locations, vacancy_location_is_eligible
from operations.models import OperationalRun
from operations.services import begin_run, finish_run
from operations.parameters import processing_is_paused
from matching.recovery import claim_analysis, enqueue_analysis, reconcile_pending_analyses, release_analysis, expire_discovery_if_due

logger = logging.getLogger(__name__)


@transaction.atomic
def create_analysis(profile: Profile, vacancy: Vacancy, config: MatchingConfig | None = None, *, force=False):
    profile = Profile.objects.select_for_update().filter(pk=profile.pk).first()
    if profile is None:
        return None
    if not profile.cv_file or profile.revision_number == 0:
        return None
    revision = profile.revisions.filter(version=profile.revision_number).first()
    if revision is None:
        return None
    if not vacancy_location_is_eligible(vacancy, revision):
        return None
    discovery, _ = ProfileVacancyDiscovery.objects.get_or_create(
        profile=profile,
        vacancy=vacancy,
        defaults={"auto_discard_threshold": profile.min_score or 0},
    )
    if expire_discovery_if_due(discovery, profile, vacancy, timezone.now()):
        return None
    config = config or get_active_matching_config()
    prior = VacancyAnalysis.objects.filter(
        profile=profile,
        vacancy=vacancy,
        profile_revision=revision,
        matching_config=config,
    )
    if not force and prior.filter(status=VacancyAnalysis.Status.COMPLETED).exists():
        return None
    if not force and prior.filter(status=VacancyAnalysis.Status.FAILED).exists():
        return None
    pending = prior.filter(status=VacancyAnalysis.Status.PENDING).first()
    if pending:
        return pending
    return VacancyAnalysis.objects.create(
        profile=profile,
        profile_revision=revision,
        vacancy=vacancy,
        matching_config=config,
    )


@shared_task(name="matching.tasks.schedule_vacancy_analysis")
def schedule_vacancy_analysis(
    vacancy_id,
    force_reanalysis=False,
    profile_ids=None,
    expected_revision_ids=None,
    expected_matching_config_id=None,
):
    if processing_is_paused():
        schedule_vacancy_analysis.apply_async(
            args=(vacancy_id, force_reanalysis, profile_ids, expected_revision_ids, expected_matching_config_id),
            countdown=60,
        )
        return []
    vacancy = Vacancy.objects.filter(pk=vacancy_id, is_active=True).first()
    if vacancy is None:
        logger.info("Se omite el análisis de la vacante %s: no existe o está inactiva.", vacancy_id)
        return []
    config = get_active_matching_config()
    if expected_matching_config_id is not None and config.pk != int(expected_matching_config_id):
        logger.info(
            "Se omite el análisis compartido de vacante %s: cambió la configuración de búsqueda.",
            vacancy_id,
        )
        return []
    queued = []
    selected_profile_ids = None if profile_ids is None else {int(value) for value in profile_ids}
    if selected_profile_ids is not None and force_reanalysis:
        selected_profile_ids.update(
            vacancy.profile_discoveries.filter(profile__owner__is_active=True).values_list("profile_id", flat=True)
        )
    profiles = Profile.objects.select_related("owner").filter(cv_file__gt="", owner__is_active=True)
    if selected_profile_ids is not None:
        profiles = profiles.filter(pk__in=selected_profile_ids)
    expected_revision_ids = expected_revision_ids or {}
    for profile in profiles:
        expected_revision_id = expected_revision_ids.get(str(profile.pk))
        if expected_revision_id is not None:
            current_revision_id = profile.revisions.filter(version=profile.revision_number).values_list("pk", flat=True).first()
            if current_revision_id != int(expected_revision_id):
                logger.info(
                    "Se omite análisis compartido de vacante %s para perfil %s: cambió la revisión.",
                    vacancy_id,
                    profile.pk,
                )
                continue
        analysis = create_analysis(profile, vacancy, config=config, force=force_reanalysis)
        if analysis and enqueue_analysis(analysis.pk):
            queued.append(analysis.pk)
    return queued


@shared_task(name="matching.tasks.schedule_profile_analyses")
def schedule_profile_analyses(profile_id):
    if processing_is_paused():
        schedule_profile_analyses.apply_async(args=(profile_id,), countdown=60)
        return []
    profile = get_object_or_404(Profile.objects.select_related("owner"), pk=profile_id, owner__is_active=True)
    queued = []
    for vacancy in Vacancy.objects.filter(is_active=True).iterator():
        analysis = create_analysis(profile, vacancy)
        if analysis and enqueue_analysis(analysis.pk):
            queued.append(analysis.pk)
    return queued


@shared_task(name="matching.tasks.schedule_legacy_analyses")
def schedule_legacy_analyses(batch_size=50, repair_pending=False):
    """Queue current-profile analyses that still use an obsolete rubric or prompt."""
    if processing_is_paused():
        return []
    config = get_active_matching_config()
    if config.rubric_version < RUBRIC_VERSION:
        return []
    current_result = VacancyAnalysis.objects.filter(
        profile_id=OuterRef("profile_id"),
        vacancy_id=OuterRef("vacancy_id"),
        profile_revision__version=F("profile__revision_number"),
        matching_config__rubric_version=config.rubric_version,
        matching_config__prompt_version=config.prompt_version,
    )
    active_result = VacancyAnalysis.objects.filter(
        profile_id=OuterRef("profile_id"), vacancy_id=OuterRef("vacancy_id"),
        profile_revision__version=F("profile__revision_number"), matching_config=config,
    )
    legacy = (
        VacancyAnalysis.objects.filter(
            profile_revision__version=F("profile__revision_number"),
            profile__owner__is_active=True,
            profile__cv_file__gt="",
            vacancy__is_active=True,
        )
        .annotate(has_current_result=Exists(current_result), has_active_result=Exists(active_result))
        .filter(
            Q(status=VacancyAnalysis.Status.COMPLETED,
              matching_config__rubric_version__lt=config.rubric_version, has_current_result=False)
            | (Q(status__in=[VacancyAnalysis.Status.PENDING, VacancyAnalysis.Status.FAILED], has_active_result=False)
               & ~Q(matching_config=config))
        )
        .select_related("profile", "vacancy")
        .order_by("created_at")
    )
    queued = []
    for previous in legacy.iterator(chunk_size=200):
        if len(queued) >= batch_size:
            break
        with transaction.atomic():
            profile = Profile.objects.select_for_update().filter(pk=previous.profile_id).first()
            if profile is None:
                continue
            existing = VacancyAnalysis.objects.filter(
                profile=profile,
                vacancy_id=previous.vacancy_id,
                profile_revision__version=profile.revision_number,
                matching_config=config,
            ).first()
            if existing:
                if previous.status == VacancyAnalysis.Status.PENDING:
                    previous.status = VacancyAnalysis.Status.SUPERSEDED
                    previous.error_message = _replacement_reason(config)
                    previous.save(update_fields=["status", "error_message", "updated_at"])
                continue
            analysis = create_analysis(profile, previous.vacancy, config=config)
            if previous.status == VacancyAnalysis.Status.PENDING:
                previous.status = VacancyAnalysis.Status.SUPERSEDED
                previous.error_message = _replacement_reason(config)
                previous.save(update_fields=["status", "error_message", "updated_at"])
        if analysis and enqueue_analysis(analysis.pk):
            queued.append(analysis.pk)

    malformed = VacancyAnalysis.objects.filter(
        matching_config=config,
        profile_revision__version=F("profile__revision_number"),
        profile__owner__is_active=True,
        profile__cv_file__gt="",
        vacancy__is_active=True,
    ).filter(
        Q(status=VacancyAnalysis.Status.COMPLETED, score__gt=10)
        | Q(status=VacancyAnalysis.Status.COMPLETED, score_breakdown={})
    ).select_related("profile", "vacancy").order_by("created_at")
    for previous in malformed.iterator(chunk_size=200):
        if len(queued) >= batch_size:
            break
        queued_analysis = _replace_malformed_current_analysis(previous, config)
        if queued_analysis:
            queued.append(queued_analysis.pk)

    if repair_pending and len(queued) < batch_size:
        pending_without_breakdown = VacancyAnalysis.objects.filter(
            matching_config=config,
            profile_revision__version=F("profile__revision_number"),
            profile__owner__is_active=True,
            profile__cv_file__gt="",
            vacancy__is_active=True,
            status=VacancyAnalysis.Status.PENDING,
            score_breakdown={},
        ).select_related("profile", "vacancy").order_by("created_at")
        for previous in pending_without_breakdown.iterator(chunk_size=200):
            if len(queued) >= batch_size:
                break
            queued_analysis = _replace_malformed_current_analysis(previous, config)
            if queued_analysis:
                queued.append(queued_analysis.pk)
    return queued


def _replace_malformed_current_analysis(previous, config):
    with transaction.atomic():
        profile = Profile.objects.select_for_update().filter(pk=previous.profile_id).first()
        if profile is None:
            return None
        current = VacancyAnalysis.objects.filter(
            profile=profile,
            vacancy_id=previous.vacancy_id,
            profile_revision__version=profile.revision_number,
            matching_config=config,
        ).exclude(pk=previous.pk)
        if current.filter(status=VacancyAnalysis.Status.COMPLETED, score__lte=10).exclude(score_breakdown={}).exists():
            replacement = None
        else:
            pending = current.filter(status=VacancyAnalysis.Status.PENDING).first()
            replacement = pending or create_analysis(profile, previous.vacancy, config=config, force=True)
        previous.status = VacancyAnalysis.Status.SUPERSEDED
        previous.error_message = f"Reemplazado por un análisis válido de {_replacement_reason(config).lower()}"
        previous.save(update_fields=["status", "error_message", "updated_at"])
    if replacement:
        enqueue_analysis(replacement.pk)
    return replacement


def _replacement_reason(config):
    return (
        f"Reemplazado por la configuración v{config.version} "
        f"(rúbrica v{config.rubric_version}, prompts v{config.prompt_version})."
    )


@shared_task(bind=True, name="matching.tasks.analyze_vacancy_for_profile")
def analyze_vacancy_for_profile(self, analysis_id):
    if processing_is_paused():
        analyze_vacancy_for_profile.apply_async(args=(analysis_id,), countdown=60)
        return None
    analysis = get_object_or_404(
        VacancyAnalysis.objects.select_related("profile_revision", "profile", "vacancy", "matching_config"),
        pk=analysis_id,
    )
    if (
        analysis.matching_config.rubric_version < RUBRIC_VERSION
        or analysis.matching_config.prompt_version < PROMPT_VERSION
        or (analysis.status == VacancyAnalysis.Status.PENDING and not analysis.matching_config.is_active)
    ):
        config = get_active_matching_config()
        replacement = create_analysis(analysis.profile, analysis.vacancy, config=config)
        if analysis.status == VacancyAnalysis.Status.PENDING:
            analysis.status = VacancyAnalysis.Status.SUPERSEDED
            analysis.error_message = _replacement_reason(config)
            analysis.save(update_fields=["status", "error_message", "updated_at"])
        if replacement:
            enqueue_analysis(replacement.pk)
        return replacement.pk if replacement else None
    if analysis.status == VacancyAnalysis.Status.SUPERSEDED:
        return None
    if analysis.profile_revision.version != analysis.profile.revision_number:
        logger.info("Se omite el análisis %s porque pertenece a una versión anterior del perfil.", analysis_id)
        return None
    if not vacancy_location_is_eligible(analysis.vacancy, analysis.profile_revision):
        logger.info("Se omite el análisis %s porque la ubicación no es compatible.", analysis_id)
        return None
    if analysis.status == VacancyAnalysis.Status.COMPLETED:
        return analysis.pk
    analysis = claim_analysis(analysis_id)
    if analysis is None:
        logger.info("Se omite la entrega duplicada o no elegible del análisis %s.", analysis_id)
        return None
    run = begin_run(
        kind=OperationalRun.Kind.ANALYSIS,
        operation="vacancy_analysis",
        task_id=self.request.id or "",
    )
    try:
        profile_text = extract_revision_text(analysis.profile_revision)
        prompt = "\n\n".join(part for part in (analysis.matching_config.analysis_prompt, RUBRIC_PROMPT) if part)
        call_started = perf_counter()
        model_result = request_model_analysis(
            profile_text=profile_text,
            search_phrases=analysis.profile_revision.search_phrases,
            locations=expand_locations(analysis.profile_revision.locations),
            remote_ok=analysis.profile_revision.remote_ok,
            vacancy={
                "source": analysis.vacancy.source,
                "title": analysis.vacancy.title,
                "company": analysis.vacancy.company,
                "location": analysis.vacancy.location,
                "description": analysis.vacancy.description,
                "salary": analysis.vacancy.salary,
                "contract_type": analysis.vacancy.contract_type,
                "details": (analysis.vacancy.raw_data or {}).get("details", {}),
                "url": analysis.vacancy.original_url,
            },
            prompt=prompt,
            parameters=analysis.matching_config.parameters,
        )
        save_validated_analysis(analysis, getattr(model_result, "content", model_result))
        _record_ai_attempt(
            analysis=analysis, stage=AICallAttempt.Stage.SCORING,
            duration_ms=_elapsed_ms(call_started), outcome=AICallAttempt.Outcome.SUCCEEDED,
            input_tokens=getattr(model_result, "input_tokens", None),
            output_tokens=getattr(model_result, "output_tokens", None),
        )
        queue_organization(analysis)
    except OmniRouteError as exc:
        if "call_started" in locals():
            _record_ai_attempt(
                analysis=analysis, stage=AICallAttempt.Stage.SCORING,
                duration_ms=_elapsed_ms(call_started),
                outcome=AICallAttempt.Outcome.RETRYING if self.request.retries < self.max_retries else AICallAttempt.Outcome.FAILED,
                error_category=exc.category,
            )
        release_analysis(analysis.pk, error_message=str(exc), update_dispatch=self.request.retries < self.max_retries)
        will_retry = self.request.retries < self.max_retries
        finish_run(
            run,
            status=OperationalRun.Status.RETRYING if will_retry else OperationalRun.Status.FAILED,
            error_category=exc.category,
        )
        logger.warning(
            "vacancy_analysis_gateway_error category=%s retry=%s will_retry=%s",
            exc.category,
            self.request.retries,
            will_retry,
        )
        if will_retry:
            raise self.retry(exc=exc, countdown=60)
        raise
    except InvalidAnalysisError as exc:
        if "call_started" in locals():
            _record_ai_attempt(analysis=analysis, stage=AICallAttempt.Stage.SCORING,
                               duration_ms=_elapsed_ms(call_started), outcome=AICallAttempt.Outcome.FAILED,
                               error_category=exc.code)
        release_analysis(analysis.pk, error_message="La respuesta de IA no cumple el formato esperado.")
        finish_run(run, status=OperationalRun.Status.FAILED, error_category=exc.code)
        logger.warning("vacancy_analysis_invalid_response category=%s", exc.code)
        raise
    except ValueError:
        if "call_started" in locals():
            _record_ai_attempt(analysis=analysis, stage=AICallAttempt.Stage.SCORING,
                               duration_ms=_elapsed_ms(call_started), outcome=AICallAttempt.Outcome.FAILED,
                               error_category="analysis_invalid")
        release_analysis(analysis.pk, error_message="La respuesta de IA no cumple el formato esperado.")
        finish_run(run, status=OperationalRun.Status.FAILED, error_category="analysis_invalid")
        logger.warning("vacancy_analysis_invalid_response")
        raise
    except Exception as exc:
        if "call_started" in locals():
            _record_ai_attempt(analysis=analysis, stage=AICallAttempt.Stage.SCORING,
                               duration_ms=_elapsed_ms(call_started), outcome=AICallAttempt.Outcome.FAILED,
                               error_category="analysis_error")
        release_analysis(analysis.pk, error_message="Ocurrió un error interno durante el análisis.")
        finish_run(run, status=OperationalRun.Status.FAILED, error_category="analysis_error")
        logger.error("vacancy_analysis_failed exception_type=%s", type(exc).__name__)
        raise
    else:
        finish_run(run, status=OperationalRun.Status.SUCCEEDED, item_count=1)
    return analysis.pk


def reprocess_analysis(previous_analysis: VacancyAnalysis):
    profile = previous_analysis.profile
    vacancy = previous_analysis.vacancy
    current = create_analysis(profile, vacancy, config=get_active_matching_config(), force=True)
    if current:
        enqueue_analysis(current.pk)
    return current


def _vacancy_organization_payload(vacancy):
    details = (vacancy.raw_data or {}).get("details", {})
    return {
        "source": vacancy.source, "title": vacancy.title, "company": vacancy.company,
        "location": vacancy.location, "description": vacancy.description, "salary": vacancy.salary,
        "contract_type": vacancy.contract_type, "details": details, "url": vacancy.original_url,
    }


def _vacancy_content_hash(vacancy):
    encoded = json.dumps(_vacancy_organization_payload(vacancy), sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _elapsed_ms(started):
    return max(0, int((perf_counter() - started) * 1000))


def _record_ai_attempt(*, analysis=None, organization=None, stage, duration_ms, outcome,
                       input_tokens=None, output_tokens=None, error_category=""):
    AICallAttempt.objects.create(
        analysis=analysis, organization=organization, stage=stage, duration_ms=duration_ms,
        outcome=outcome, input_tokens=input_tokens, output_tokens=output_tokens,
        error_category=error_category[:80],
    )


@transaction.atomic
def queue_organization(analysis):
    """Queue one reusable organization result for the vacancy/config/content version."""
    analysis = VacancyAnalysis.objects.select_for_update().select_related(
        "vacancy", "matching_config", "profile"
    ).get(pk=analysis.pk)
    if analysis.status != VacancyAnalysis.Status.COMPLETED or analysis.score is None:
        return None
    discovery, _ = ProfileVacancyDiscovery.objects.select_for_update().get_or_create(
        profile=analysis.profile,
        vacancy=analysis.vacancy,
        defaults={"auto_discard_threshold": analysis.profile.min_score or 0},
    )
    if discovery.auto_discard_threshold > 0 and analysis.score < discovery.auto_discard_threshold:
        analysis.organization_status = VacancyAnalysis.OrganizationStatus.DEFERRED
        analysis.save(update_fields=["organization_status", "updated_at"])
        return None
    fingerprint = _vacancy_content_hash(analysis.vacancy)
    organization, _ = VacancyOrganization.objects.get_or_create(
        vacancy=analysis.vacancy, matching_config=analysis.matching_config, content_hash=fingerprint,
    )
    organization = VacancyOrganization.objects.select_for_update().get(pk=organization.pk)
    analysis.organization = organization
    analysis.organization_status = (
        VacancyAnalysis.OrganizationStatus.COMPLETED
        if organization.status == VacancyOrganization.Status.COMPLETED
        else VacancyAnalysis.OrganizationStatus.PENDING
    )
    analysis.save(update_fields=["organization", "organization_status", "updated_at"])
    if organization.status == VacancyOrganization.Status.COMPLETED:
        return organization
    now = timezone.now()
    if organization.last_enqueued_at and organization.last_enqueued_at > now - timedelta(minutes=5):
        return organization
    if processing_is_paused():
        return organization
    organization.status = VacancyOrganization.Status.PENDING
    organization.last_enqueued_at = now
    organization.error_message = ""
    organization.save(update_fields=["status", "last_enqueued_at", "error_message", "updated_at"])
    if not processing_is_paused():
        transaction.on_commit(lambda organization_id=organization.pk: organize_vacancy.delay(organization_id))
    return organization


@shared_task(bind=True, name="matching.tasks.organize_vacancy")
def organize_vacancy(self, organization_id):
    if processing_is_paused():
        organize_vacancy.apply_async(args=(organization_id,), countdown=60)
        return None
    organization = VacancyOrganization.objects.select_related("vacancy", "matching_config").filter(
        pk=organization_id
    ).first()
    if not organization or organization.status == VacancyOrganization.Status.COMPLETED:
        return organization_id if organization else None
    now = timezone.now()
    with transaction.atomic():
        organization = VacancyOrganization.objects.select_for_update().select_related(
            "vacancy", "matching_config"
        ).filter(pk=organization_id).first()
        if not organization or organization.status == VacancyOrganization.Status.COMPLETED:
            return organization_id if organization else None
        if organization.processing_started_at and organization.processing_started_at > now - timedelta(minutes=10):
            return None
        # Content changed after enqueue: create/queue the current version and ignore the stale work item.
        if organization.content_hash != _vacancy_content_hash(organization.vacancy):
            analyses = list(organization.analyses.filter(status=VacancyAnalysis.Status.COMPLETED))
            for analysis in analyses:
                queue_organization(analysis)
            return None
        organization.processing_started_at = now
        organization.save(update_fields=["processing_started_at", "updated_at"])
    started = perf_counter()
    try:
        result = request_model_organization(
            vacancy=_vacancy_organization_payload(organization.vacancy),
            prompt=organization.matching_config.organization_prompt,
            parameters=organization.matching_config.parameters,
        )
        save_validated_organization(organization, getattr(result, "content", result))
        _record_ai_attempt(
            organization=organization, stage=AICallAttempt.Stage.ORGANIZATION,
            duration_ms=_elapsed_ms(started), outcome=AICallAttempt.Outcome.SUCCEEDED,
            input_tokens=getattr(result, "input_tokens", None),
            output_tokens=getattr(result, "output_tokens", None),
        )
    except OmniRouteError as exc:
        will_retry = self.request.retries < self.max_retries
        _record_ai_attempt(
            organization=organization, stage=AICallAttempt.Stage.ORGANIZATION,
            duration_ms=_elapsed_ms(started), outcome=AICallAttempt.Outcome.RETRYING if will_retry else AICallAttempt.Outcome.FAILED,
            error_category=exc.category,
        )
        organization.processing_started_at = None
        organization.error_message = "La organización no está disponible temporalmente."
        if not will_retry:
            organization.status = VacancyOrganization.Status.FAILED
            organization.analyses.update(organization_status=VacancyAnalysis.OrganizationStatus.FAILED)
        organization.save(update_fields=["processing_started_at", "error_message", "status", "updated_at"])
        if will_retry:
            raise self.retry(exc=exc, countdown=60)
        raise
    except (InvalidAnalysisError, ValueError) as exc:
        _record_ai_attempt(
            organization=organization, stage=AICallAttempt.Stage.ORGANIZATION,
            duration_ms=_elapsed_ms(started), outcome=AICallAttempt.Outcome.FAILED,
            error_category="organization_invalid",
        )
        organization.status = VacancyOrganization.Status.FAILED
        organization.processing_started_at = None
        organization.error_message = "La respuesta de organización no cumple el formato esperado."
        organization.save(update_fields=["status", "processing_started_at", "error_message", "updated_at"])
        organization.analyses.update(organization_status=VacancyAnalysis.OrganizationStatus.FAILED)
        raise
    except Exception as exc:
        _record_ai_attempt(
            organization=organization, stage=AICallAttempt.Stage.ORGANIZATION,
            duration_ms=_elapsed_ms(started), outcome=AICallAttempt.Outcome.FAILED,
            error_category="organization_error",
        )
        organization.status = VacancyOrganization.Status.FAILED
        organization.processing_started_at = None
        organization.error_message = "Ocurrió un error interno durante la organización."
        organization.save(update_fields=["status", "processing_started_at", "error_message", "updated_at"])
        organization.analyses.update(organization_status=VacancyAnalysis.OrganizationStatus.FAILED)
        logger.error("vacancy_organization_failed exception_type=%s", type(exc).__name__)
        raise
    return organization_id


@shared_task(name="matching.tasks.retry_failed_organizations")
def retry_failed_organizations(batch_size=50):
    if processing_is_paused():
        return 0
    queued = 0
    active_config = get_active_matching_config()
    candidates = VacancyOrganization.objects.filter(
        status=VacancyOrganization.Status.FAILED,
        matching_config=active_config,
    ).order_by("updated_at")[:batch_size]
    for organization in candidates:
        if organization.recovery_count >= 3:
            continue
        organization.status = VacancyOrganization.Status.PENDING
        organization.recovery_count += 1
        organization.last_enqueued_at = None
        organization.save(update_fields=["status", "recovery_count", "last_enqueued_at", "updated_at"])
        for analysis in organization.analyses.filter(status=VacancyAnalysis.Status.COMPLETED).select_related("profile"):
            queue_organization(analysis)
        queued += 1
    return queued


@shared_task(name="matching.tasks.reconcile_organizations")
def reconcile_organizations(batch_size=50):
    if processing_is_paused():
        return 0
    stale_cutoff = timezone.now() - timedelta(minutes=10)
    candidates = VacancyOrganization.objects.filter(status=VacancyOrganization.Status.PENDING).filter(
        Q(last_enqueued_at__isnull=True) | Q(last_enqueued_at__lt=stale_cutoff)
    ).filter(Q(processing_started_at__isnull=True) | Q(processing_started_at__lt=stale_cutoff)).order_by("updated_at")[:batch_size]
    queued = 0
    for organization in candidates:
        analyses = organization.analyses.filter(
            status=VacancyAnalysis.Status.COMPLETED
        ).select_related("profile", "vacancy", "matching_config")
        for analysis in analyses:
            if queue_organization(analysis):
                queued += 1
                break
    return queued


@shared_task(name="matching.tasks.schedule_eligible_organizations")
def schedule_eligible_organizations(profile_id):
    if processing_is_paused():
        return []
    profile = Profile.objects.filter(pk=profile_id, owner__is_active=True).first()
    if profile is None:
        return []
    analyses = VacancyAnalysis.objects.filter(
        profile=profile,
        profile_revision__version=profile.revision_number,
        matching_config__rubric_version=RUBRIC_VERSION,
        status=VacancyAnalysis.Status.COMPLETED,
    ).select_related("vacancy", "matching_config", "profile")
    queued = []
    revision = profile.revisions.filter(version=profile.revision_number).first()
    for analysis in analyses:
        if revision and vacancy_location_is_eligible(analysis.vacancy, revision):
            organization = queue_organization(analysis)
            if organization:
                queued.append(organization.pk)
    return list(dict.fromkeys(queued))


@shared_task(name="matching.tasks.reconcile_pending_analyses")
def reconcile_pending_analyses_task(batch_size=None):
    if processing_is_paused():
        return 0
    return reconcile_pending_analyses(batch_size=batch_size)
