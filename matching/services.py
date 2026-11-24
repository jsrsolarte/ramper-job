from copy import deepcopy
from dataclasses import dataclass
import logging

from django.db import transaction

from .client import request_model_title_preselection
from .evidence import PROFILE_EVIDENCE_ANALYSIS_INSTRUCTION, ensure_profile_artifacts
from .models import (
    CRITICAL_REQUIREMENT_DEDUCTION,
    DEFAULT_SEARCH_PROMPT,
    RUBRIC_CRITERIA,
    RUBRIC_VERSION,
    MatchingConfig,
    PROMPT_VERSION,
    default_matching_parameters,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TitlePreselectionResult:
    listings: list
    discarded_count: int = 0
    input_tokens: int | None = None

CONCISE_ANALYSIS_INSTRUCTION = (
    "En evidence, reasons y gaps incluye solo la evidencia o razón principal que sustenta cada resultado. "
    "Evita repetir la misma idea y omite contexto que no cambie el puntaje. Conserva cada campo requerido, "
    "toda evidencia necesaria para justificar puntajes y deducciones, y no inventes información."
)
CONCISE_ORGANIZATION_INSTRUCTION = (
    "Consolida ideas repetidas y conserva cada dato distinto que ayude a comparar la vacante. "
    "Omite comentarios auxiliares y explicaciones redundantes; no elimines categorías respaldadas "
    "por la publicación ni infieras información ausente."
)
CRITICAL_COMPLETENESS_INSTRUCTION = (
    "Enumera en critical_requirements cada requisito explícito obligatorio, incluso los que se cumplen; "
    "no omitas ninguno por brevedad. Para cada elemento usa requirement de máximo 180 caracteres, "
    "evidence de máximo 240 caracteres y status exactamente uno de: cumple, sin_evidencia o contradicho. "
    "Incluye evidencia breve para cada uno; si status es contradicho, la evidencia debe mostrar una "
    "incompatibilidad explícita."
)
EVIDENCE_STATUS_INSTRUCTION = (
    "La falta de experiencia o una trayectoria en otro sector no contradice un requisito: usa sin_evidencia. "
    "Reserva contradicho para evidencia explícita de incompatibilidad."
)

DEFAULT_ANALYSIS_PROMPT = (
    "Compara la hoja de vida y los criterios del perfil con los requisitos y responsabilidades de la vacante. "
    "Evalúa solo evidencia disponible; no inventes experiencia, requisitos ni credenciales. "
    f"{CONCISE_ANALYSIS_INSTRUCTION} {CRITICAL_COMPLETENESS_INSTRUCTION} {EVIDENCE_STATUS_INSTRUCTION}"
)
DEFAULT_ORGANIZATION_PROMPT = (
    "Organiza únicamente la información de la publicación. Devuelve JSON con summary (máximo 300 caracteres), "
    "keywords, responsibilities, requirements y conditions como listas concisas. "
    f"Incluye solo datos respaldados por el texto y no añadas hechos. {CONCISE_ORGANIZATION_INSTRUCTION}"
)

RUBRIC_PROMPT = """
Evalúa usando exclusivamente esta rúbrica común, versión 3, en escala de 0 a 5. No otorgues puntos por ubicación ni modalidad. No devuelvas un puntaje total; la aplicación suma los criterios y aplica las deducciones.

Criterios y máximos: skills 2,0; experience 1,0; alignment 1,0; education 0,5; profile_criteria 0,5. Evalúa la misma evidencia laboral de cada criterio proporcionalmente a esos máximos. En education y profile_criteria, si no hay requisito explícito, asigna el máximo con no_aplica.

Para cada criterio devuelve score con precisión de 0,05 como máximo, status y evidence breve (hasta 240 caracteres). Estados: cumple, parcial, sin_evidencia, contradicho, no_aplica. Usa cumple solo para el máximo; parcial solo para puntajes intermedios; sin_evidencia y contradicho reciben 0; contradicho requiere evidencia. No uses no_aplica salvo para education o profile_criteria, que reciben su máximo.

Enumera aparte critical_requirements solo para requisitos explícitos y obligatorios. Usa requirement, status (cumple, sin_evidencia o contradicho) y evidence. La aplicación resta 1,0 punto por cada requisito obligatorio contradicho. La falta de información no es contradicción y no genera deducción. No uses discapacidad, edad, sexo, género, origen, religión, situación familiar ni otros atributos personales para puntuar o deducir. Devuelve rubric_version=3.
""".strip()


def rubric_prompt(version):
    if version != RUBRIC_VERSION:
        raise ValueError("No hay un prompt activo para una versión antigua de rúbrica.")
    return RUBRIC_PROMPT


@transaction.atomic
def get_active_matching_config():
    config = MatchingConfig.objects.select_for_update().filter(is_active=True).order_by("-version").first()
    if config and config.rubric_version == RUBRIC_VERSION and config.prompt_version >= PROMPT_VERSION:
        return config
    latest_version = MatchingConfig.objects.order_by("-version").values_list("version", flat=True).first() or 0
    parameters = deepcopy(config.parameters) if config else default_matching_parameters()
    if not config or config.rubric_version != RUBRIC_VERSION:
        parameters.pop("weights", None)
        parameters["rubric"] = default_matching_parameters()["rubric"]
    if config:
        config.is_active = False
        config.save(update_fields=["is_active"])
    return MatchingConfig.objects.create(
        version=latest_version + 1,
        rubric_version=RUBRIC_VERSION,
        prompt_version=PROMPT_VERSION,
        search_prompt=config.search_prompt if config else DEFAULT_SEARCH_PROMPT,
        analysis_prompt=_versioned_prompt(
            _versioned_prompt(
                _versioned_prompt(
                    _versioned_prompt(
                        config.analysis_prompt if config else DEFAULT_ANALYSIS_PROMPT,
                        CONCISE_ANALYSIS_INSTRUCTION,
                    ),
                    CRITICAL_COMPLETENESS_INSTRUCTION,
                ),
                EVIDENCE_STATUS_INSTRUCTION,
            ),
            PROFILE_EVIDENCE_ANALYSIS_INSTRUCTION,
        ),
        organization_prompt=_versioned_prompt(
            config.organization_prompt if config else DEFAULT_ORGANIZATION_PROMPT,
            CONCISE_ORGANIZATION_INSTRUCTION,
        ),
        parameters=parameters,
        is_active=True,
    )


def _versioned_prompt(existing_prompt, concise_instruction):
    prompt = (existing_prompt or "").strip()
    if concise_instruction in prompt:
        return prompt
    return "\n\n".join(part for part in (prompt, concise_instruction) if part)


def get_profile_search_terms(profile_revision, config=None):
    config = config or get_active_matching_config()
    _evidence, search_terms = ensure_profile_artifacts(profile_revision, config)
    return search_terms


def preselect_listing_titles(listings, search_terms):
    """Discard only titles with one explicit, valid, clear-incompatibility decision."""
    listings = list(listings)
    if not listings:
        return TitlePreselectionResult(listings=[])

    kept = []
    total_tokens = 0
    tokens_known = True
    for offset in range(0, len(listings), 50):
        batch = listings[offset:offset + 50]
        submitted = [
            {"id": str(offset + index), "title": str(listing.title or "")[:240]}
            for index, listing in enumerate(batch)
        ]
        try:
            response = request_model_title_preselection(
                search_terms=[str(term)[:160] for term in search_terms[:30]],
                vacancies=submitted,
            )
        except Exception as exc:
            logger.info("vacancy_title_preselection_fallback exception_type=%s", type(exc).__name__)
            kept.extend(batch)
            tokens_known = False
            continue

        content = getattr(response, "content", response)
        decisions = content.get("decisions") if isinstance(content, dict) else None
        response_tokens = getattr(response, "input_tokens", None)
        if response_tokens is None:
            tokens_known = False
        else:
            total_tokens += response_tokens
        if not isinstance(decisions, list):
            kept.extend(batch)
            continue

        decisions_by_id = {}
        for decision in decisions:
            if isinstance(decision, dict) and isinstance(decision.get("id"), str):
                decisions_by_id.setdefault(decision["id"], []).append(decision.get("classification"))

        for index, listing in enumerate(batch):
            decision_values = decisions_by_id.get(str(offset + index), [])
            # Discard only one explicit clear-mismatch label; uncertainty fails open.
            if len(decision_values) == 1 and decision_values[0] == "clearly_unrelated":
                continue
            kept.append(listing)
    return TitlePreselectionResult(
        listings=kept,
        discarded_count=len(listings) - len(kept),
        input_tokens=total_tokens if tokens_known else None,
    )
