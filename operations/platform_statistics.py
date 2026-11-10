from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from math import ceil

from django.db.models import Count, Exists, F, Min, OuterRef, Q, Subquery
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from matching.models import AICallAttempt, VacancyAnalysis

from .models import OperationalRun


SCORE_PERIODS = {
    "24h": ("24 horas", timedelta(hours=24)),
    "7d": ("7 días", timedelta(days=7)),
    "30d": ("30 días", timedelta(days=30)),
}
DEFAULT_SCORE_PERIOD = "30d"

FORMAT_FAILURE_LABELS = {
    "analysis_invalid": "Formato inválido (registro histórico)",
    "omniroute.invalid_json": "La respuesta no es JSON válido",
    "analysis.schema.not_object": "La respuesta JSON no es un objeto",
    "analysis.rubric.version": "Versión de rúbrica incorrecta",
    "analysis.rubric.criteria_set": "Criterios de rúbrica ausentes o adicionales",
    "analysis.rubric.critical_requirements.not_list": "Requisitos críticos: formato de lista",
    "analysis.rubric.critical_requirement.not_object": "Requisito crítico: formato de objeto",
    "analysis.rubric.critical_requirement.text_invalid": "Requisito crítico: texto inválido",
    "analysis.rubric.critical_requirement.status_invalid": "Requisito crítico: estado inválido",
    "analysis.rubric.critical_requirement.evidence_invalid": "Requisito crítico: evidencia inválida",
    "analysis.rubric.critical_requirement.evidence_required": "Requisito crítico: falta evidencia",
    "analysis.rubric.reasons.not_string_list": "Razones: formato de lista",
    "analysis.rubric.gaps.not_string_list": "Brechas: formato de lista",
}
RUBRIC_CRITERION_LABELS = {
    "skills": "habilidades", "experience": "experiencia", "alignment": "alineación",
    "education": "educación", "profile_criteria": "criterios del perfil",
}
RUBRIC_RULE_LABELS = {
    "not_object": "estructura inválida", "score_not_numeric": "puntaje no numérico",
    "score_out_of_range": "puntaje fuera de rango", "score_precision": "precisión del puntaje",
    "status_invalid": "estado inválido", "evidence_invalid": "evidencia inválida",
    "status_score_mismatch": "estado y puntaje incompatibles", "evidence_required": "falta evidencia",
}


def _format_failure_label(code):
    label = FORMAT_FAILURE_LABELS.get(code)
    if label:
        return label
    parts = code.split(".")
    if len(parts) == 4 and parts[:2] == ["analysis", "rubric"]:
        criterion = RUBRIC_CRITERION_LABELS.get(parts[2])
        rule = RUBRIC_RULE_LABELS.get(parts[3])
        if criterion and rule:
            return f"{criterion.capitalize()}: {rule}"
    return None


def _median_from_counts(score_counts, sample_size):
    """Return an exact median from grouped decimal scores, without loading rows."""
    targets = ((sample_size - 1) // 2, sample_size // 2)
    found = []
    offset = 0
    ordered_scores = sorted(score_counts)
    for score in ordered_scores:
        next_offset = offset + score_counts[score]
        while len(found) < 2 and targets[len(found)] < next_offset:
            found.append(score)
        if len(found) == 2:
            break
        offset = next_offset
    if not found:
        return None
    if len(found) == 1:
        found.append(found[0])
    return ((found[0] + found[1]) / Decimal("2")).quantize(Decimal("0.01"))


def _duration_percentiles(durations):
    """Return median and nearest-rank p95 for a non-empty list of ms durations."""
    ordered = sorted(durations)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[middle]
    else:
        median = round((ordered[middle - 1] + ordered[middle]) / 2)
    p95 = ordered[max(0, ceil(len(ordered) * 0.95) - 1)]
    return median, p95


def _score_distribution(grouped_rows):
    scores_by_rubric = defaultdict(dict)
    for row in grouped_rows:
        version = row["matching_config__rubric_version"]
        scores_by_rubric[version][row["score"]] = row["count"]

    distributions = []
    for version in sorted(scores_by_rubric, key=lambda value: (value is None, value or 0)):
        score_counts = scores_by_rubric[version]
        sample_size = sum(score_counts.values())
        maximum = max(score_counts.values(), default=0)
        bands = []
        for lower in range(10):
            upper = lower + 1
            if upper == 10:
                count = sum(n for score, n in score_counts.items() if Decimal(lower) <= score <= Decimal("10"))
                label = f"{lower}–10"
            else:
                count = sum(n for score, n in score_counts.items() if Decimal(lower) <= score < Decimal(upper))
                label = f"{lower}–<{upper}"
            bands.append({
                "label": label,
                "count": count,
                "width_percent": round(count * 100 / maximum) if maximum else 0,
            })
        distributions.append({
            "rubric_version": version,
            "rubric_label": f"Rúbrica {version}" if version is not None and version > 0 else "Rúbrica sin versión",
            "sample_size": sample_size,
            "median": _median_from_counts(score_counts, sample_size),
            "bands": bands,
        })
    return distributions


def build_platform_statistics(*, period="30d", now=None):
    """Build anonymous business statistics for the platform admin dashboard."""
    now = now or timezone.now()
    if period not in SCORE_PERIODS:
        period = DEFAULT_SCORE_PERIOD
    period_label, period_delta = SCORE_PERIODS[period]
    requested_start = now - period_delta

    finished_source_queries = OperationalRun.objects.filter(
        kind=OperationalRun.Kind.INGESTION,
        operation="source_query",
        started_at__gte=requested_start,
        started_at__lte=now,
        finished_at__isnull=False,
    ).exclude(source="")
    source_query_summaries = list(finished_source_queries.values("source").annotate(
        total=Count("pk"),
        non_successful=Count(
            "pk",
            filter=Q(status__in=(
                OperationalRun.Status.PARTIAL,
                OperationalRun.Status.RETRYING,
                OperationalRun.Status.FAILED,
            )),
        ),
    ).order_by("source"))
    durations_by_source = defaultdict(list)
    for source, duration_ms in finished_source_queries.filter(
        duration_ms__isnull=False,
    ).order_by("source", "duration_ms").values_list("source", "duration_ms"):
        durations_by_source[source].append(duration_ms)

    source_performance = []
    for summary in source_query_summaries:
        durations = durations_by_source[summary["source"]]
        median_ms, p95_ms = _duration_percentiles(durations) if durations else (None, None)
        source_performance.append({
            "source": summary["source"],
            "total": summary["total"],
            "median_seconds": median_ms / 1000 if median_ms is not None else None,
            "p95_seconds": p95_ms / 1000 if p95_ms is not None else None,
            "non_successful_percent": (summary["non_successful"] * 100 / summary["total"])
            if summary["total"] else 0,
        })

    tracking_counts = {status: 0 for status, _label in VacancyFollowUp.Status.choices}
    for row in VacancyFollowUp.objects.filter(
        archived_at__isnull=True,
    ).values("status").annotate(count=Count("pk")):
        if row["status"] in tracking_counts:
            tracking_counts[row["status"]] = row["count"]

    completed = VacancyAnalysis.objects.filter(status=VacancyAnalysis.Status.COMPLETED)
    latest_completed = completed.filter(
        profile_id=OuterRef("profile_id"),
        vacancy_id=OuterRef("vacancy_id"),
    ).order_by("-completed_at", "-pk").values("pk")[:1]
    any_follow_up = VacancyFollowUp.objects.filter(
        profile_id=OuterRef("profile_id"), vacancy_id=OuterRef("vacancy_id"),
        archived_at__isnull=True,
    )
    implicit_pending = completed.annotate(
        latest_result_id=Subquery(latest_completed),
        has_follow_up=Exists(any_follow_up),
    ).filter(
        pk=F("latest_result_id"), has_follow_up=False,
    ).values("profile_id", "vacancy_id").distinct().count()
    tracking_counts[VacancyFollowUp.Status.PENDING] += implicit_pending
    tracking_total = sum(tracking_counts.values())
    tracking_states = [
        {"value": status, "label": label, "count": tracking_counts[status]}
        for status, label in VacancyFollowUp.Status.choices
    ]
    tracking_scale = max(tracking_counts.values(), default=0) or 1
    for state in tracking_states:
        state["width_percent"] = round(state["count"] * 100 / tracking_scale)

    coverage_start = AICallAttempt.objects.filter(
        stage=AICallAttempt.Stage.SCORING,
    ).aggregate(first=Min("created_at"))["first"]
    coverage_start = timezone.localtime(coverage_start) if coverage_start else None
    coverage_complete = bool(coverage_start and requested_start >= coverage_start)
    effective_start = max(requested_start, coverage_start) if coverage_start else None

    distributions = []
    if effective_start:
        current_completed = completed.annotate(
            latest_result_id=Subquery(latest_completed),
        ).filter(pk=F("latest_result_id"))
        grouped_scores = current_completed.filter(
            completed_at__gte=effective_start,
            completed_at__lte=now,
            score__gte=0,
            score__lte=10,
        ).exclude(score_breakdown={}).values(
            "matching_config__rubric_version", "score",
        ).annotate(count=Count("pk"))
        distributions = _score_distribution(grouped_scores)

    format_failures = []
    if effective_start:
        attempts = AICallAttempt.objects.filter(
            stage=AICallAttempt.Stage.SCORING,
            outcome__in=[AICallAttempt.Outcome.FAILED, AICallAttempt.Outcome.RETRYING],
            created_at__gte=effective_start,
            created_at__lte=now,
        ).values("error_category").annotate(count=Count("pk"))
        for row in attempts:
            label = _format_failure_label(row["error_category"])
            if label:
                format_failures.append({"code": row["error_category"], "label": label, "count": row["count"]})
        format_failures.sort(key=lambda item: (-item["count"], item["label"]))

    return {
        "cutoff_at": timezone.localtime(now),
        "tracking_states": tracking_states,
        "tracking_total": tracking_total,
        "period": period,
        "period_label": period_label,
        "periods": SCORE_PERIODS,
        "source_performance": source_performance,
        "has_source_performance": bool(source_performance),
        "requested_start": timezone.localtime(requested_start),
        "coverage_start": coverage_start,
        "coverage_complete": coverage_complete,
        "score_distributions": distributions,
        "has_score_data": any(item["sample_size"] for item in distributions),
        "format_failures": format_failures,
        "has_format_failures": bool(format_failures),
    }
