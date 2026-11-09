from profiles.models import GuidedTourProgress
from profiles.tour import TOUR_VERSION


def mark_tour_completed(*users):
    """Treat fixture accounts as users migrated from before mandatory onboarding."""
    GuidedTourProgress.objects.bulk_create([
        GuidedTourProgress(
            owner=user,
            version=TOUR_VERSION,
            status=GuidedTourProgress.Status.NOT_STARTED,
            mandatory_completed=True,
        )
        for user in users
    ])
