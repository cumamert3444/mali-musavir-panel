from rest_framework import serializers

from apps.pos_sync.models import DailyPosReport


class DailyPosReportSerializer(serializers.ModelSerializer):
    client_title = serializers.CharField(source="client.title", read_only=True)
    total_sales_incl_vat = serializers.ReadOnlyField()

    class Meta:
        model = DailyPosReport
        fields = [
            "id", "client", "client_title", "report_date", "okc_no",
            "gross_sales", "vat_amount", "pos_collection", "cash_collection",
            "total_sales_incl_vat", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
