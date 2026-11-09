import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


DEBUG = env_bool("DJANGO_DEBUG", True)
if DEBUG:
    SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-local-development-key")
else:
    SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
    if not SECRET_KEY:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatorio cuando DJANGO_DEBUG está desactivado")
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "config.apps.PlatformAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "profiles",
    "jobs",
    "matching",
    "dashboard",
    "operations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "config.middleware.LogoutInactiveUsersMiddleware",
    "config.middleware.MandatoryGuidedTourMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "ramper_job"),
        "USER": os.getenv("POSTGRES_USER", "ramper_job"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "ramper_job_local"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("POSTGRES_CONN_MAX_AGE", "60")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_ROOT = Path(os.getenv("PRIVATE_MEDIA_ROOT", BASE_DIR / "media"))
MEDIA_URL = "/private-media/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "login"
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
PASSWORD_RESET_TIMEOUT = int(os.getenv("PASSWORD_RESET_TIMEOUT", "259200"))

SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", not DEBUG)
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_TIMEZONE = TIME_ZONE
JOB_REFRESH_MINUTES = int(os.getenv("JOB_REFRESH_MINUTES", "120"))
from operations.schedules import DatabaseRefreshInterval
from celery.schedules import crontab

CELERY_TASK_ROUTES = {
    "dashboard.tasks.discard_stale_recommendations": {"queue": "matching_v2"},
    "dashboard.tasks.archive_inactive_follow_ups": {"queue": "matching_v2"},
    "jobs.tasks.refresh_profile_sources": {"queue": "matching_v2"},
    "jobs.tasks.refresh_sources": {"queue": "matching_v2"},
    "operations.tasks.cleanup_operational_history": {"queue": "matching_v2"},
    "matching.tasks.analyze_vacancy_for_profile": {"queue": "matching_v2"},
    "matching.tasks.schedule_legacy_analyses": {"queue": "matching_v2"},
    "matching.tasks.schedule_profile_analyses": {"queue": "matching_v2"},
    "matching.tasks.schedule_vacancy_analysis": {"queue": "matching_v2"},
    "matching.tasks.reconcile_pending_analyses": {"queue": "matching_v2"},
    "matching.tasks.organize_vacancy": {"queue": "matching_v2"},
    "matching.tasks.schedule_eligible_organizations": {"queue": "matching_v2"},
    "matching.tasks.retry_failed_organizations": {"queue": "matching_v2"},
    "matching.tasks.reconcile_organizations": {"queue": "matching_v2"},
}
CELERY_BEAT_SCHEDULE = {
    "discard-stale-recommendations": {
        "task": "dashboard.tasks.discard_stale_recommendations",
        "schedule": crontab(hour=3, minute=0),
    },
    "archive-inactive-follow-ups": {
        "task": "dashboard.tasks.archive_inactive_follow_ups",
        "schedule": crontab(hour=3, minute=30),
    },
    "refresh-job-sources": {
        "task": "jobs.tasks.refresh_sources",
        "schedule": DatabaseRefreshInterval(),
    },
    "reprocess-legacy-matching-analyses": {
        "task": "matching.tasks.schedule_legacy_analyses",
        "schedule": int(os.getenv("MATCHING_REPROCESS_SECONDS", "60")),
    },
    "recover-stale-pending-analyses": {
        "task": "matching.tasks.reconcile_pending_analyses",
        "schedule": int(os.getenv("ANALYSIS_RECOVERY_INTERVAL_SECONDS", "60")),
    },
    "recover-stale-vacancy-organizations": {
        "task": "matching.tasks.reconcile_organizations",
        "schedule": 5 * 60,
    },
    "retry-failed-vacancy-organizations": {
        "task": "matching.tasks.retry_failed_organizations",
        "schedule": 15 * 60,
    },
    "cleanup-operational-history": {
        "task": "operations.tasks.cleanup_operational_history",
        "schedule": 24 * 60 * 60,
    },
}
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 15 * 60
ANALYSIS_RECOVERY_INTERVAL_SECONDS = int(os.getenv("ANALYSIS_RECOVERY_INTERVAL_SECONDS", "60"))
ANALYSIS_RECOVERY_STALE_SECONDS = int(os.getenv("ANALYSIS_RECOVERY_STALE_SECONDS", "300"))
ANALYSIS_RECOVERY_LEASE_SECONDS = int(os.getenv("ANALYSIS_RECOVERY_LEASE_SECONDS", "1200"))
ANALYSIS_RECOVERY_BATCH_SIZE = int(os.getenv("ANALYSIS_RECOVERY_BATCH_SIZE", "50"))

ELEMPLEO_SEARCH_URL = os.getenv("ELEMPLEO_SEARCH_URL", "https://www.elempleo.com/co/ofertas-empleo")
OMNIROUTE_BASE_URL = os.getenv("OMNIROUTE_BASE_URL", "")
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "")
OMNIROUTE_MODEL = os.getenv("OMNIROUTE_MODEL", "")
OMNIROUTE_TIMEOUT_SECONDS = int(os.getenv("OMNIROUTE_TIMEOUT_SECONDS", "180"))
OMNIROUTE_CHAT_COMPLETIONS_PATH = os.getenv("OMNIROUTE_CHAT_COMPLETIONS_PATH") or "chat/completions"
