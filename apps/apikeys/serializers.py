from rest_framework import serializers

from apps.apikeys.models import ApiKey


class ApiKeySerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)

    class Meta:
        model = ApiKey
        fields = [
            "id", "name", "prefix", "scopes", "is_active",
            "created_by_email", "last_used_at", "expires_at", "created_at",
        ]
        read_only_fields = fields


class ApiKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    expires_at = serializers.DateTimeField(required=False, allow_null=True, default=None)


class ApiKeyCreatedResponseSerializer(serializers.ModelSerializer):
    """Sadece olusturma yanitinda kullanilir; `key` alani bir daha asla
    donulmeyecek olan ham API anahtaridir."""

    key = serializers.CharField()

    class Meta:
        model = ApiKey
        fields = ["id", "name", "prefix", "key", "expires_at", "created_at"]
