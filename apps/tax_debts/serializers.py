from rest_framework import serializers

from apps.tax_debts.models import TaxDebtRecord


class TaxDebtRecordSerializer(serializers.ModelSerializer):
    client_title = serializers.CharField(source="client.title", read_only=True)
    client_tax_number = serializers.CharField(source="client.tax_number", read_only=True)

    class Meta:
        model = TaxDebtRecord
        fields = [
            "id", "client", "client_title", "client_tax_number", "debt_type", "period_label",
            "description", "amount", "due_date", "status", "source", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "source", "created_at", "updated_at"]
