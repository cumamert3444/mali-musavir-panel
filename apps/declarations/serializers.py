from rest_framework import serializers

from apps.declarations.models import ClientDeclarationSubscription, DeclarationInstance, DeclarationType


class DeclarationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeclarationType
        fields = [
            "id", "code", "name", "period", "due_month_offset", "due_day",
            "description", "is_active",
        ]


class ClientDeclarationSubscriptionSerializer(serializers.ModelSerializer):
    declaration_type_detail = DeclarationTypeSerializer(source="declaration_type", read_only=True)

    class Meta:
        model = ClientDeclarationSubscription
        fields = ["id", "client", "declaration_type", "declaration_type_detail", "is_active", "starts_on"]
        read_only_fields = ["id", "client"]


class DeclarationInstanceSerializer(serializers.ModelSerializer):
    client_title = serializers.CharField(source="client.title", read_only=True)
    declaration_type_name = serializers.CharField(source="declaration_type.name", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeclarationInstance
        fields = [
            "id", "client", "client_title", "declaration_type", "declaration_type_name",
            "period_label", "period_start", "period_end", "due_date",
            "status", "submitted_at", "completed_by", "notes", "is_overdue",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "client", "declaration_type", "period_label", "period_start",
                             "period_end", "due_date", "created_at", "updated_at"]
