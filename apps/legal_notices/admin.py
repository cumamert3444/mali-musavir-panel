from django.contrib import admin

from apps.legal_notices.models import LegalNotification


@admin.register(LegalNotification)
class LegalNotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "office", "client", "source", "status", "received_at", "response_due_date"]
    list_filter = ["office", "source", "status"]
    search_fields = ["title", "notification_number", "client__title"]
    date_hierarchy = "received_at"
