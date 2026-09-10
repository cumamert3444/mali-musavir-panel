from rest_framework import serializers

from apps.core.models import AccountCodeMemory, AuditLog


class AccountCodeMemorySerializer(serializers.ModelSerializer):
    source_app_display = serializers.CharField(source="get_source_app_display", read_only=True)

    class Meta:
        model = AccountCodeMemory
        fields = [
            "id", "source_app", "source_app_display", "match_key", "account_code",
            "hit_count", "created_at", "last_used_at",
        ]
        read_only_fields = ["id", "hit_count", "created_at", "last_used_at"]


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
