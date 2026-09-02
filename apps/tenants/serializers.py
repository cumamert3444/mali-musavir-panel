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

    user_count = serializers.SerializerMethodField()
    client_count = serializers.SerializerMethodField()

    class Meta(OfficeSerializer.Meta):
        fields = OfficeSerializer.Meta.fields + ["user_count", "client_count"]
        read_only_fields = ["slug", "created_at", "updated_at"]

    def get_user_count(self, obj):
        return obj.memberships.filter(is_active=True).count()

    def get_client_count(self, obj):
        return obj.clients_client_set.count()


class SubscriptionPlanAdminSerializer(serializers.ModelSerializer):
    """Süper admin'in paket/fiyatlandırma tanımlarını yönetmesi için."""

    office_count = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "code", "name", "max_users", "max_clients",
            "price_monthly", "api_access_included", "features", "is_active", "office_count",
        ]

    def get_office_count(self, obj):
        return obj.subscriptions.count()
