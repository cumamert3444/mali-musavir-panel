from django.contrib import admin

from apps.core.models import AccountCodeMemory, AuditLog


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


@admin.register(AccountCodeMemory)
class AccountCodeMemoryAdmin(admin.ModelAdmin):
    list_display = ("office", "source_app", "match_key", "account_code", "hit_count", "last_used_at")
    list_filter = ("source_app", "office")
    search_fields = ("match_key", "account_code")
