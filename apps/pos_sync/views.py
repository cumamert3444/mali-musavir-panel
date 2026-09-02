import csv
import io

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.clients.models import Client
from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.pos_sync.models import DailyPosReport
from apps.pos_sync.serializers import DailyPosReportSerializer


class DailyPosReportViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """POS & ÖKC gün sonu raporları -- bkz. apps.pos_sync.models.DailyPosReport
    docstring'i."""

    queryset = DailyPosReport.objects.select_related("client")
    serializer_class = DailyPosReportSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_fields = ["client"]
    search_fields = ["client__title", "okc_no"]
    ordering_fields = ["report_date", "gross_sales"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office)
        log_action(self.request, action="create", model_name="DailyPosReport", object_id=instance.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request, action="update", model_name="DailyPosReport", object_id=instance.id)

    def perform_destroy(self, instance):
        log_action(self.request, action="delete", model_name="DailyPosReport", object_id=instance.id)
        instance.delete()

    @action(detail=False, methods=["get"])
    def monthly_summary(self, request):
        """`GET .../pos-reports/monthly_summary/?year=2026&month=8` --
        müşteri bazında aylık toplam net satış/KDV/tahsilat özeti."""
        try:
            year = int(request.query_params.get("year"))
            month = int(request.query_params.get("month"))
        except (TypeError, ValueError):
            return Response({"detail": "'year' ve 'month' parametreleri zorunludur."}, status=400)

        queryset = self.get_queryset().filter(report_date__year=year, report_date__month=month)
        by_client: dict[int, dict] = {}
        for report in queryset:
            bucket = by_client.setdefault(
                report.client_id,
                {"client_id": report.client_id, "client_title": report.client.title,
                 "gross_sales": 0, "vat_amount": 0, "pos_collection": 0, "cash_collection": 0, "day_count": 0},
            )
            bucket["gross_sales"] = float(bucket["gross_sales"]) + float(report.gross_sales)
            bucket["vat_amount"] = float(bucket["vat_amount"]) + float(report.vat_amount)
            bucket["pos_collection"] = float(bucket["pos_collection"]) + float(report.pos_collection)
            bucket["cash_collection"] = float(bucket["cash_collection"]) + float(report.cash_collection)
            bucket["day_count"] += 1

        rows = sorted(by_client.values(), key=lambda b: -b["gross_sales"])
        return Response({"year": year, "month": month, "rows": rows})

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        """`POST .../pos-reports/import-csv/` -- multipart 'file' alanıyla
        toplu gün sonu raporu içe aktarır. Beklenen kolonlar:
        client_tax_number, report_date, okc_no, gross_sales, vat_amount, pos_collection, cash_collection, notes"""
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "'file' alanı ile bir CSV dosyası yükleyin."}, status=400)
        try:
            decoded = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response({"detail": "Dosya UTF-8 formatında olmalı."}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        clients_by_tax_no = {
            c.tax_number: c for c in Client.objects.filter(office=request.office).exclude(tax_number="")
        }

        created, errors = [], []
        for row_num, row in enumerate(reader, start=2):
            tax_no = (row.get("client_tax_number") or "").strip()
            client = clients_by_tax_no.get(tax_no)
            if not client:
                errors.append(f"Satır {row_num}: vergi no '{tax_no}' ile eşleşen müşteri bulunamadı.")
                continue
            try:
                report, created_flag = DailyPosReport.objects.update_or_create(
                    office=request.office,
                    client=client,
                    report_date=(row.get("report_date") or "").strip(),
                    okc_no=(row.get("okc_no") or "").strip(),
                    defaults={
                        "gross_sales": (row.get("gross_sales") or "0").strip().replace(",", "."),
                        "vat_amount": (row.get("vat_amount") or "0").strip().replace(",", "."),
                        "pos_collection": (row.get("pos_collection") or "0").strip().replace(",", "."),
                        "cash_collection": (row.get("cash_collection") or "0").strip().replace(",", "."),
                        "notes": (row.get("notes") or "").strip(),
                    },
                )
                created.append(report.id)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Satır {row_num}: {exc}")

        log_action(request, action="create", model_name="DailyPosReport",
                   metadata={"event": "csv_import", "created": len(created), "errors": len(errors)})
        return Response({"created_count": len(created), "error_count": len(errors), "errors": errors}, status=201 if created else 400)
