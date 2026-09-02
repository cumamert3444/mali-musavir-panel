import csv
import io

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.clients.models import Client
from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.tax_debts.models import TaxDebtRecord
from apps.tax_debts.serializers import TaxDebtRecordSerializer

CSV_COLUMNS = ["client_tax_number", "debt_type", "period_label", "description", "amount", "due_date", "status", "notes"]


class TaxDebtRecordViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Vergi/SGK Borç Matrisi -- bkz. apps.tax_debts.models.TaxDebtRecord
    docstring'i (Tek Hamle tarzı konsolide borç takibi)."""

    queryset = TaxDebtRecord.objects.select_related("client")
    serializer_class = TaxDebtRecordSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_fields = ["client", "debt_type", "status"]
    search_fields = ["client__title", "description", "period_label"]
    ordering_fields = ["due_date", "amount", "created_at"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office, source=TaxDebtRecord.Source.MANUAL)
        log_action(self.request, action="create", model_name="TaxDebtRecord", object_id=instance.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request, action="update", model_name="TaxDebtRecord", object_id=instance.id)

    def perform_destroy(self, instance):
        log_action(self.request, action="delete", model_name="TaxDebtRecord", object_id=instance.id)
        instance.delete()

    @action(detail=False, methods=["get"])
    def matrix(self, request):
        """`GET .../tax-debts/matrix/?status=unpaid` -- müşteri bazında
        konsolide borç matrisi: her mükellefin borç türü kırılımı + toplamı."""
        queryset = self.get_queryset()
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            queryset = queryset.exclude(status=TaxDebtRecord.Status.PAID)

        by_client: dict[int, dict] = {}
        for record in queryset.order_by("client__title"):
            bucket = by_client.setdefault(
                record.client_id,
                {"client_id": record.client_id, "client_title": record.client.title, "total": 0, "breakdown": {}, "count": 0},
            )
            bucket["total"] = float(bucket["total"]) + float(record.amount)
            bucket["count"] += 1
            bucket["breakdown"][record.debt_type] = float(bucket["breakdown"].get(record.debt_type, 0)) + float(record.amount)

        rows = sorted(by_client.values(), key=lambda b: -b["total"])
        grand_total = sum(r["total"] for r in rows)
        return Response({
            "grand_total": grand_total,
            "client_count": len(rows),
            "rows": rows,
        })

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        """`POST .../tax-debts/import-csv/` -- multipart 'file' alanıyla
        toplu borç kaydı içe aktarır. Beklenen kolonlar:
        client_tax_number, debt_type, period_label, description, amount, due_date, status, notes
        (client_tax_number zorunlu, o vergi numarasına sahip müşteri bu ofiste bulunmalı)."""
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "'file' alanı ile bir CSV dosyası yükleyin."}, status=400)

        try:
            decoded = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response({"detail": "Dosya UTF-8 formatında olmalı."}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        valid_debt_types = {c for c, _ in TaxDebtRecord.DebtType.choices}
        valid_statuses = {c for c, _ in TaxDebtRecord.Status.choices}

        created, errors = [], []
        clients_by_tax_no = {
            c.tax_number: c for c in Client.objects.filter(office=request.office).exclude(tax_number="")
        }

        for row_num, row in enumerate(reader, start=2):
            tax_no = (row.get("client_tax_number") or "").strip()
            client = clients_by_tax_no.get(tax_no)
            if not client:
                errors.append(f"Satır {row_num}: vergi no '{tax_no}' ile eşleşen müşteri bulunamadı.")
                continue
            try:
                amount = row.get("amount", "").strip().replace(",", ".")
                record = TaxDebtRecord.objects.create(
                    office=request.office,
                    client=client,
                    debt_type=row.get("debt_type", "vergi").strip() if row.get("debt_type", "").strip() in valid_debt_types else "vergi",
                    period_label=(row.get("period_label") or "").strip(),
                    description=(row.get("description") or "").strip(),
                    amount=amount,
                    due_date=(row.get("due_date") or "").strip() or None,
                    status=row.get("status", "unpaid").strip() if row.get("status", "").strip() in valid_statuses else "unpaid",
                    notes=(row.get("notes") or "").strip(),
                    source=TaxDebtRecord.Source.CSV_IMPORT,
                )
                created.append(record.id)
            except Exception as exc:  # noqa: BLE001 -- kullanıcıya satır bazlı hata dönmek için genis yakalama
                errors.append(f"Satır {row_num}: {exc}")

        log_action(request, action="create", model_name="TaxDebtRecord",
                   metadata={"event": "csv_import", "created": len(created), "errors": len(errors)})
        return Response({"created_count": len(created), "error_count": len(errors), "errors": errors}, status=201 if created else 400)
