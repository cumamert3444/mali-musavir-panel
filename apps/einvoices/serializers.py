from rest_framework import serializers

from apps.einvoices.models import EInvoiceRecord


class EInvoiceRecordSerializer(serializers.ModelSerializer):
    client_title = serializers.CharField(source="client.title", read_only=True)
    client_tax_number = serializers.CharField(source="client.tax_number", read_only=True)

    class Meta:
        model = EInvoiceRecord
        fields = [
            "id", "client", "client_title", "client_tax_number",
            "doc_type", "direction", "invoice_number",
            "counterparty_title", "counterparty_tax_number",
            "amount", "currency", "issue_date", "period_label",
            "status", "source", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "source", "created_at", "updated_at"]
