from django.apps import AppConfig


class MatchingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "matching"
    verbose_name = "Compatibilidad"

    def ready(self):
        from . import signals  # noqa: F401
