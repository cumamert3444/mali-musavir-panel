from rest_framework import serializers

from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor_label",
            "action",
            "action_display",
            "model_name",
            "object_id",
            "method",
            "path",
            "ip_address",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
