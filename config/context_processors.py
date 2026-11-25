import os

from profiles.models import Profile


def app_version(_request):
    """Expose the deployment-provided identifier without inventing a fallback."""
    value = os.getenv("APP_VERSION", "").strip()
    return {"app_version": value or None}


def recommendation_notifications(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or user.is_staff or user.is_superuser:
        return {"recommendation_new_count": 0, "recommendation_new_cutoff": 0}
    profile = Profile.objects.filter(owner=user).first()
    if not profile:
        return {"recommendation_new_count": 0, "recommendation_new_cutoff": 0}

    from dashboard.services import new_recommendation_summary

    summary = new_recommendation_summary(profile)
    return {
        "recommendation_new_count": summary["count"],
        "recommendation_new_cutoff": summary["cutoff"],
    }
