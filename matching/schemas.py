from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone

from .models import (
    CRITICAL_REQUIREMENT_DEDUCTION,
    RUBRIC_CRITERIA,
    RUBRIC_STATUSES,
    RUBRIC_VERSION,
)


class InvalidAnalysisError(ValueError):
    """The model returned a response outside the agreed analysis schema."""

    def __init__(self, code: str, message: str):
        # Codes are constants from this module; never derive them from model data.
        self.code = code
        super().__init__(message)


class InvalidSearchKeywordsError(ValueError):
    """The model returned an invalid set of search keywords."""


def validate_search_keywords(payload: dict) -> list[str]:
    if not isinstance(payload, dict):
        raise InvalidSearchKeywordsError("La respuesta de búsqueda debe ser un objeto JSON.")
    keywords = payload.get("keywords")
    if not isinstance(keywords, list):
        raise InvalidSearchKeywordsError("Las palabras clave deben venir en una lista.")
    normalized, seen = [], set()
    for item in keywords:
        if not isinstance(item, str):
            raise InvalidSearchKeywordsError("Cada palabra clave debe ser texto.")
        term = " ".join(item.split())
        if not term or len(term) > 100:
            raise InvalidSearchKeywordsError("Cada palabra clave debe contener entre 1 y 100 caracteres.")
        if term.casefold() not in seen:
            normalized.append(term)
            seen.add(term.casefold())
        if len(normalized) > 5:
            raise InvalidSearchKeywordsError("El modelo no puede devolver más de cinco palabras clave.")
    return normalized


def validate_analysis(payload: dict, *, rubric_version: int = RUBRIC_VERSION,
                      critical_deduction=CRITICAL_REQUIREMENT_DEDUCTION) -> dict:
    if not isinstance(payload, dict):
        raise InvalidAnalysisError("analysis.schema.not_object", "La respuesta debe ser un objeto JSON.")
    response_version = payload.get("rubric_version")
    if (isinstance(response_version, bool) or not isinstance(response_version, int)
            or response_version != rubric_version):
        raise InvalidAnalysisError("analysis.rubric.version", "La respuesta no corresponde a la versión de rúbrica solicitada.")
    score_breakdown = _validate_score_breakdown(payload.get("score_breakdown"))
    critical_requirements = _validate_critical_requirements(payload.get("critical_requirements"))
    deduction_per_requirement = Decimal(str(critical_deduction))
    deductions = [
        {"requirement": item["requirement"], "evidence": item["evidence"], "points": deduction_per_requirement}
        for item in critical_requirements if item["status"] == "contradicho"
    ]
    raw_total = sum((item["score"] for item in score_breakdown.values()), Decimal("0.0"))
    total = max(Decimal("0.0"), min(Decimal("10.0"), raw_total - sum(
        (item["points"] for item in deductions), Decimal("0.0")
    ))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return {
        "score": total,
        "score_breakdown": score_breakdown,
        "critical_requirements": critical_requirements,
        "deductions": deductions,
        "reasons": _string_list(payload.get("reasons"), "razones"),
        "gaps": _string_list(payload.get("gaps"), "brechas"),
    }


def _validate_score_breakdown(value):
    if not isinstance(value, dict) or set(value) != set(RUBRIC_CRITERIA):
        raise InvalidAnalysisError("analysis.rubric.criteria_set", "El desglose debe incluir exactamente los cinco criterios de la rúbrica.")
    validated = {}
    for key, definition in RUBRIC_CRITERIA.items():
        item = value.get(key)
        if not isinstance(item, dict):
            raise InvalidAnalysisError(f"analysis.rubric.{key}.not_object", f"El criterio {key} debe ser un objeto.")
        raw_points, status, evidence = item.get("score"), item.get("status"), item.get("evidence")
        try:
            points = Decimal(str(raw_points))
        except (InvalidOperation, ValueError):
            raise InvalidAnalysisError(f"analysis.rubric.{key}.score_not_numeric", f"El puntaje de {key} debe ser numérico.") from None
        maximum = Decimal(str(definition["max_score"]))
        if isinstance(raw_points, bool) or not points.is_finite() or points < 0 or points > maximum:
            raise InvalidAnalysisError(f"analysis.rubric.{key}.score_out_of_range", f"El puntaje de {key} debe estar entre 0 y {maximum}.")
        if points != points.quantize(Decimal("0.1")):
            raise InvalidAnalysisError(f"analysis.rubric.{key}.score_precision", f"El puntaje de {key} admite como máximo una cifra decimal.")
        if status not in RUBRIC_STATUSES:
            raise InvalidAnalysisError(f"analysis.rubric.{key}.status_invalid", f"El estado de evidencia de {key} no es válido.")
        if not isinstance(evidence, str) or len(evidence.strip()) > 240:
            raise InvalidAnalysisError(f"analysis.rubric.{key}.evidence_invalid", f"La evidencia de {key} debe ser texto de hasta 240 caracteres.")
        evidence = evidence.strip()
        if status == "no_aplica":
            if key not in {"education", "profile_criteria"} or points != maximum:
                raise InvalidAnalysisError(f"analysis.rubric.{key}.status_score_mismatch", f"El criterio {key} no puede marcarse como no aplicable con ese puntaje.")
        elif status in {"sin_evidencia", "contradicho"} and points != 0:
            raise InvalidAnalysisError(f"analysis.rubric.{key}.status_score_mismatch", f"El criterio {key} debe recibir cero puntos si no hay evidencia o está contradicho.")
        elif status == "cumple" and points != maximum:
            raise InvalidAnalysisError(f"analysis.rubric.{key}.status_score_mismatch", f"El criterio {key} debe recibir su máximo de puntos si se cumple completamente.")
        elif status == "parcial" and not 0 < points < maximum:
            raise InvalidAnalysisError(f"analysis.rubric.{key}.status_score_mismatch", f"El criterio {key} debe tener un puntaje parcial menor que su máximo.")
        if (points > 0 or status == "contradicho") and not evidence:
            raise InvalidAnalysisError(f"analysis.rubric.{key}.evidence_required", f"El criterio {key} requiere evidencia para justificar su estado o puntaje.")
        validated[key] = {"score": points, "max_score": maximum, "status": status, "evidence": evidence}
    return validated


def _validate_critical_requirements(value):
    if not isinstance(value, list):
        raise InvalidAnalysisError("analysis.rubric.critical_requirements.not_list", "Los requisitos críticos deben venir en una lista.")
    validated, seen = [], set()
    for item in value:
        if not isinstance(item, dict):
            raise InvalidAnalysisError("analysis.rubric.critical_requirement.not_object", "Cada requisito crítico debe ser un objeto.")
        requirement = item.get("requirement")
        status = item.get("status")
        evidence = item.get("evidence", "")
        if not isinstance(requirement, str) or not requirement.strip() or len(requirement.strip()) > 180:
            raise InvalidAnalysisError("analysis.rubric.critical_requirement.text_invalid", "Cada requisito crítico debe tener texto de hasta 180 caracteres.")
        requirement = " ".join(requirement.split())
        if status not in {"cumple", "sin_evidencia", "contradicho"}:
            raise InvalidAnalysisError("analysis.rubric.critical_requirement.status_invalid", "El estado del requisito crítico no es válido.")
        if not isinstance(evidence, str) or len(evidence.strip()) > 240:
            raise InvalidAnalysisError("analysis.rubric.critical_requirement.evidence_invalid", "La evidencia crítica debe ser texto de hasta 240 caracteres.")
        evidence = evidence.strip()
        if status == "contradicho" and not evidence:
            raise InvalidAnalysisError("analysis.rubric.critical_requirement.evidence_required", "Un requisito crítico contradicho requiere evidencia explícita.")
        key = requirement.casefold()
        if key not in seen:
            validated.append({"requirement": requirement, "status": status, "evidence": evidence})
            seen.add(key)
    return validated


def validate_organization(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise InvalidAnalysisError("analysis.organization.not_object", "La organización debe ser un objeto JSON.")
    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise InvalidAnalysisError("analysis.organization.summary_invalid", "El resumen organizado debe incluir texto.")
    return {
        "summary": summary.strip()[:300],
        "keywords": _string_list(payload.get("keywords", []), "palabras clave"),
        "responsibilities": _string_list(payload.get("responsibilities", []), "responsabilidades"),
        "requirements": _string_list(payload.get("requirements", []), "requisitos"),
        "conditions": _string_list(payload.get("conditions", []), "condiciones"),
    }


def _string_list(value, label):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        # Labels are internal constants at call sites and are not model values.
        safe_label = {"razones": "reasons", "brechas": "gaps", "palabras clave": "keywords",
                      "responsabilidades": "responsibilities", "requisitos": "requirements",
                      "condiciones": "conditions"}.get(label, "list")
        namespace = "analysis.organization" if safe_label in {"keywords", "responsibilities", "requirements", "conditions"} else "analysis.rubric"
        raise InvalidAnalysisError(f"{namespace}.{safe_label}.not_string_list", f"{label.capitalize()} debe ser una lista de textos.")
    return [item.strip()[:220].rstrip() for item in value if item.strip()][:5]


@transaction.atomic
def save_validated_analysis(analysis, payload: dict):
    parameters = analysis.matching_config.parameters or {}
    rubric_params = parameters.get("rubric") or {}
    result = validate_analysis(
        payload,
        rubric_version=analysis.matching_config.rubric_version,
        critical_deduction=rubric_params.get("critical_requirement_deduction", CRITICAL_REQUIREMENT_DEDUCTION),
    )
    analysis.score = result["score"]
    score_breakdown = {
        key: {
            **item,
            "score": float(item["score"]),
            "max_score": float(item["max_score"]),
        }
        for key, item in result["score_breakdown"].items()
    }
    analysis.score_breakdown = {
        **score_breakdown,
        "critical_requirements": result["critical_requirements"],
        "deductions": [
            {**item, "points": float(item["points"])} for item in result["deductions"]
        ],
        "deduction_per_critical_requirement": str(rubric_params.get(
            "critical_requirement_deduction", CRITICAL_REQUIREMENT_DEDUCTION
        )),
    }
    analysis.reasons = result["reasons"]
    analysis.gaps = result["gaps"]
    analysis.error_message = ""
    analysis.status = analysis.Status.COMPLETED
    analysis.completed_at = timezone.now()
    analysis.organization_status = analysis.OrganizationStatus.DEFERRED
    analysis.processing_started_at = None
    analysis.save(update_fields=[
        "score", "score_breakdown", "reasons", "gaps", "error_message", "status",
        "organization_status", "processing_started_at", "completed_at", "updated_at",
    ])
    from dashboard.services import apply_discovery_score_threshold

    apply_discovery_score_threshold(analysis.profile, analysis.vacancy, analysis.score)
    return analysis


def save_validated_organization(organization, payload: dict):
    content = validate_organization(payload)
    organization.content = content
    organization.status = organization.Status.COMPLETED
    organization.error_message = ""
    organization.processing_started_at = None
    organization.save(update_fields=["content", "status", "error_message", "processing_started_at", "updated_at"])
    organization.analyses.update(organization_status="completed")
    return organization
