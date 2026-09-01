from rest_framework import serializers

from apps.tenants.models import Office, Subscription, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "code", "name", "max_users", "max_clients",
            "price_monthly", "api_access_included", "features", "is_active",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "plan", "status", "trial_ends_at", "current_period_end"]


class OfficeSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = Office
        fields = [
            "id", "name", "slug", "legal_name", "tax_number", "tax_office",
            "address", "phone", "email", "is_active", "api_enabled",
            "subscription", "created_at", "updated_at",
        ]
        read_only_fields = ["slug", "is_active", "created_at", "updated_at"]


class OfficeAdminSerializer(OfficeSerializer):
    """Sadece super admin'in kullanacagi, is_active/api_enabled'i de
    degistirebildigi tam yetkili serializer."""

    class Meta(OfficeSerializer.Meta):
        read_only_fields = ["slug", "created_at", "updated_at"]
