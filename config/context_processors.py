import os


def app_version(_request):
    """Expose the deployment-provided identifier without inventing a fallback."""
    value = os.getenv("APP_VERSION", "").strip()
    return {"app_version": value or None}
