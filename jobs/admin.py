from django.contrib import admin

from .models import JobSourceStatus, Vacancy


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "source", "is_active", "last_seen_at")
    list_filter = ("source", "is_active", "contract_type")
    search_fields = ("title", "company", "location", "description")
    readonly_fields = ("first_seen_at", "last_seen_at")


@admin.register(JobSourceStatus)
class JobSourceStatusAdmin(admin.ModelAdmin):
    list_display = ("source", "available", "last_checked_at", "last_success_at", "last_vacancy_count")
    readonly_fields = tuple(field.name for field in JobSourceStatus._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
