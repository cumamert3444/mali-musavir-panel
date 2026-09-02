from django.contrib import admin

from apps.leads.models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "office_name", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["full_name", "email", "office_name"]
