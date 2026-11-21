"""Read-only per-applicant statistics for the administration area."""

from django.db.models import Count, F, Max, OuterRef, Subquery
from django.utils import timezone

from dashboard.models import VacancyFollowUp
from dashboard.services import current_score_analyses, dashboard_follow_up_counts
from matching.models import ProfileVacancyDiscovery, VacancyAnalysis


def _localtime(value):
    return timezone.localtime(value) if value else None


def build_applicant_statistics(profile, *, now=None):
    """Build only the individual counters defined by the OpenSpec contract."""
    now = now or timezone.now()
    follow_up_counts = {status: 0 for status, _label in VacancyFollowUp.Status.choices}
    analysis_counts = {
        VacancyAnalysis.Status.PENDING: 0,
        VacancyAnalysis.Status.COMPLETED: 0,
        VacancyAnalysis.Status.FAILED: 0,
    }
    archived_count = 0
    discovered_count = 0
    latest_discovery = None
    historical_completed_count = 0
    latest_historical_completion = None

    revision = None
    if profile:
        current_dashboard_analyses, revision, _archived_ids = current_score_analyses(profile)
        follow_up_counts = dashboard_follow_up_counts(profile, current_dashboard_analyses)
        archived_count = VacancyFollowUp.objects.filter(
            profile=profile,
            archived_at__isnull=False,
        ).count()

        if revision:
            latest_analysis = VacancyAnalysis.objects.filter(
                profile=profile,
                vacancy=OuterRef("vacancy"),
                profile_revision=revision,
            ).order_by("-created_at", "-pk").values("pk")[:1]
            current_analyses = VacancyAnalysis.objects.filter(
                profile=profile,
                profile_revision=revision,
            ).annotate(latest_id=Subquery(latest_analysis)).filter(pk=F("latest_id"))
            for row in current_analyses.values("status").annotate(total=Count("pk")):
                if row["status"] in analysis_counts:
                    analysis_counts[row["status"]] = row["total"]

        discovery_summary = ProfileVacancyDiscovery.objects.filter(profile=profile).aggregate(
            total=Count("pk"),
            latest=Max("first_found_at"),
        )
        discovered_count = discovery_summary["total"]
        latest_discovery = discovery_summary["latest"]

        completed_summary = VacancyAnalysis.objects.filter(
            profile=profile,
            status=VacancyAnalysis.Status.COMPLETED,
        ).aggregate(
            total=Count("pk"),
            latest=Max("completed_at"),
        )
        historical_completed_count = completed_summary["total"]
        latest_historical_completion = completed_summary["latest"]

    follow_up_states = [
        {"value": status, "label": label, "count": follow_up_counts[status]}
        for status, label in VacancyFollowUp.Status.choices
    ]
    return {
        "has_profile": profile is not None,
        "queried_at": _localtime(now),
        "follow_up_states": follow_up_states,
        "follow_up_total": sum(follow_up_counts.values()),
        "archived_count": archived_count,
        "analysis_counts": analysis_counts,
        "analysis_total": sum(analysis_counts.values()),
        "analysis_unit_label": "análisis vigentes de la revisión actual, máximo uno por vacante",
        "discovered_count": discovered_count,
        "latest_discovery": _localtime(latest_discovery),
        "historical_completed_count": historical_completed_count,
        "latest_historical_completion": _localtime(latest_historical_completion),
    }
