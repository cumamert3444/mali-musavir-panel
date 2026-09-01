from django.contrib import admin

from apps.apikeys.models import ApiKey


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "office", "prefix", "is_active", "created_by", "last_used_at", "expires_at"]
    list_filter = ["is_active", "office"]
    search_fields = ["name", "prefix", "office__name"]
    readonly_fields = ["prefix", "hashed_key", "last_used_at"]
