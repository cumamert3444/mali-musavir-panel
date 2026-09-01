from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "office", "recipient", "channel", "category", "is_read", "sent_at", "created_at"]
    list_filter = ["office", "channel", "category", "is_read"]
    search_fields = ["title", "recipient__email"]
