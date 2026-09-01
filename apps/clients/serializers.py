from rest_framework import serializers

from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from apps.clients.models import (
    Client,
    ClientAssignment,
    ClientContact,
    ClientGroup,
    Contract,
    ServicePackage,
)


class ServicePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePackage
        fields = ["id", "name", "description", "default_monthly_fee", "is_active"]


class ClientGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientGroup
        fields = ["id", "name", "color"]


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = [
            "id", "client", "title", "status", "start_date", "end_date",
            "auto_renew", "monthly_fee", "scope_description", "file", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "client", "created_at", "updated_at"]


class ClientContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientContact
        fields = ["id", "client", "full_name", "role", "phone", "email", "is_primary"]
        read_only_fields = ["id", "client"]


class ClientAssignmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user", queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = ClientAssignment
        fields = ["id", "client", "user", "user_id", "role", "created_at"]
        read_only_fields = ["id", "client", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ofis uyeleriyle sinirlamak icin queryset'i context'ten daralt.
        office = self.context.get("office")
        if office is not None:
            self.fields["user_id"].queryset = User.objects.filter(memberships__office=office, is_active=True)
        else:
            self.fields["user_id"].queryset = User.objects.all()


class ClientListSerializer(serializers.ModelSerializer):
    package_name = serializers.CharField(source="package.name", read_only=True, default=None)
    groups = ClientGroupSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = [
            "id", "title", "legal_type", "status", "tax_number", "city",
            "package", "package_name", "monthly_fee", "employee_count",
            "e_invoice_enabled", "e_ledger_enabled", "groups", "created_at",
        ]


class ClientDetailSerializer(serializers.ModelSerializer):
    contacts = ClientContactSerializer(many=True, read_only=True)
    assignments = ClientAssignmentSerializer(many=True, read_only=True)
    contracts = ContractSerializer(many=True, read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True, default=None)
    groups = ClientGroupSerializer(many=True, read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        source="groups", queryset=ClientGroup.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Client
        fields = [
            "id", "title", "legal_type", "status",
            "tax_number", "tax_office", "mersis_no", "trade_registry_no",
            "address", "city", "phone", "email",
            "package", "package_name", "monthly_fee", "employee_count",
            "e_invoice_enabled", "e_ledger_enabled", "accounting_software",
            "start_date", "end_date", "notes",
            "groups", "group_ids", "contacts", "assignments", "contracts",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        office = getattr(request, "office", None) if request is not None else None
        if office is not None:
            self.fields["group_ids"].queryset = ClientGroup.objects.filter(office=office)
