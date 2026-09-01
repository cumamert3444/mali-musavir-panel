from django.contrib import admin

from apps.core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "office", "actor_label", "action", "model_name", "object_id", "path")
    list_filter = ("action", "office")
    search_fields = ("actor_label", "model_name", "object_id", "path")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
