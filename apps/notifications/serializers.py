from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "channel", "category", "title", "body",
            "related_object_type", "related_object_id",
            "is_read", "sent_at", "created_at",
        ]
        read_only_fields = fields
