from rest_framework import serializers

from apps.invoicing.models import InvoiceLine, Payment, ServiceInvoice


class InvoiceLineSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceLine
        fields = ["id", "invoice", "description", "quantity", "unit_price", "amount"]
        read_only_fields = ["id", "invoice"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "invoice", "amount", "method", "paid_at", "reference", "created_at"]
        read_only_fields = ["id", "invoice", "created_at"]


class ServiceInvoiceSerializer(serializers.ModelSerializer):
    client_title = serializers.CharField(source="client.title", read_only=True)
    lines = InvoiceLineSerializer(many=True, required=False)
    payments = PaymentSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ServiceInvoice
        fields = [
            "id", "client", "client_title", "invoice_number", "period_label",
            "issue_date", "due_date", "status", "notes",
            "lines", "payments", "total_amount", "paid_amount", "balance_due",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", [])
        invoice = ServiceInvoice.objects.create(**validated_data)
        for line_data in lines_data:
            InvoiceLine.objects.create(invoice=invoice, **line_data)
        return invoice

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                InvoiceLine.objects.create(invoice=instance, **line_data)
        return instance
