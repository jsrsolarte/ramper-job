from django.contrib import admin, messages
from django.db import transaction
from decimal import Decimal, InvalidOperation

from .models import AICallAttempt, PROMPT_VERSION, RUBRIC_VERSION, MatchingConfig, VacancyAnalysis, VacancyOrganization, default_matching_parameters
from .tasks import reprocess_analysis


@admin.register(MatchingConfig)
class MatchingConfigAdmin(admin.ModelAdmin):
    list_display = ("version", "is_active", "created_at")
    list_display_links = None
    fields = ("search_prompt", "analysis_prompt", "organization_prompt", "parameters")

    def get_changeform_initial_data(self, request):
        active = MatchingConfig.objects.filter(is_active=True).order_by("-version").first()
        if active:
            return {
                "search_prompt": active.search_prompt,
                "analysis_prompt": active.analysis_prompt,
                "organization_prompt": active.organization_prompt,
                "parameters": active.parameters,
            }
        return super().get_changeform_initial_data(request)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            MatchingConfig.objects.filter(is_active=True).update(is_active=False)
            latest = MatchingConfig.objects.order_by("-version").values_list("version", flat=True).first() or 0
            obj.pk = None
            obj._state.adding = True
            obj.version = latest + 1
            obj.rubric_version = RUBRIC_VERSION
            obj.prompt_version = PROMPT_VERSION
            obj.parameters = obj.parameters or default_matching_parameters()
            obj.parameters.pop("weights", None)
            rubric_settings = (obj.parameters.get("rubric") or {})
            deduction = rubric_settings.get(
                "critical_requirement_deduction",
                default_matching_parameters()["rubric"]["critical_requirement_deduction"],
            )
            try:
                deduction = Decimal(str(deduction))
            except (InvalidOperation, ValueError):
                deduction = Decimal("2.0")
            if not deduction.is_finite() or deduction < 0 or deduction > 10 or deduction != deduction.quantize(Decimal("0.1")):
                deduction = Decimal("2.0")
            obj.parameters["rubric"] = default_matching_parameters()["rubric"]
            obj.parameters["rubric"]["critical_requirement_deduction"] = str(deduction)
            obj.is_active = True
            obj.save()

    def has_change_permission(self, request, obj=None):
        return False


@admin.action(description="Reprocesar con el perfil y la configuración vigentes")
def reprocess_selected_analyses(modeladmin, request, queryset):
    queued = 0
    for previous in queryset.select_related("profile", "vacancy"):
        if reprocess_analysis(previous):
            queued += 1
    modeladmin.message_user(request, f"Se programaron {queued} análisis nuevos.", messages.SUCCESS)


@admin.register(VacancyAnalysis)
class VacancyAnalysisAdmin(admin.ModelAdmin):
    list_display = ("profile", "vacancy", "status", "score", "matching_config", "created_at")
    list_filter = ("status", "matching_config", "vacancy__source")
    search_fields = ("profile__owner__username", "vacancy__title", "vacancy__company")
    readonly_fields = tuple(field.name for field in VacancyAnalysis._meta.fields)
    actions = (reprocess_selected_analyses,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(VacancyOrganization)
class VacancyOrganizationAdmin(admin.ModelAdmin):
    list_display = ("vacancy", "matching_config", "status", "recovery_count", "updated_at")
    list_filter = ("status", "matching_config")
    readonly_fields = tuple(field.name for field in VacancyOrganization._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AICallAttempt)
class AICallAttemptAdmin(admin.ModelAdmin):
    list_display = ("stage", "outcome", "duration_ms", "input_tokens", "output_tokens", "created_at")
    list_filter = ("stage", "outcome", "error_category")
    readonly_fields = tuple(field.name for field in AICallAttempt._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
