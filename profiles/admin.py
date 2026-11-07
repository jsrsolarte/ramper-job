from django.contrib import admin

from .models import Profile, ProfileRevision


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("owner", "revision_number", "updated_at")
    search_fields = ("owner__username", "owner__email")
    readonly_fields = ("revision_number", "updated_at")


@admin.register(ProfileRevision)
class ProfileRevisionAdmin(admin.ModelAdmin):
    list_display = ("profile", "version", "created_at")
    readonly_fields = (
        "profile", "version", "search_phrases", "locations", "remote_ok", "cv_file_path", "created_at"
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
