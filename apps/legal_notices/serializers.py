from rest_framework import serializers

from apps.legal_notices.models import LegalNotification


class LegalNotificationSerializer(serializers.ModelSerializer):
    client_title = serializers.CharField(source="client.title", read_only=True, default=None)
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True, default=None)

    class Meta:
        model = LegalNotification
        fields = [
            "id", "client", "client_title", "source", "notification_number",
            "title", "body_summary", "received_at", "response_due_date",
            "status", "assigned_to", "assigned_to_email", "document", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
