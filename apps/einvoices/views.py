import csv
import io

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.clients.models import Client
from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.einvoices.models import EInvoiceRecord
from apps.einvoices.serializers import EInvoiceRecordSerializer

CSV_COLUMNS = [
    "client_tax_number", "doc_type", "direction", "invoice_number",
    "counterparty_title", "counterparty_tax_number", "amount", "currency",
    "issue_date", "period_label", "status", "notes",
]


class EInvoiceRecordViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """e-Fatura Kayıtları -- bkz. apps.einvoices.models.EInvoiceRecord
    docstring'i (dürüst kapsam notu: CSV/Excel içe aktarma, gerçek zamanlı
    GİB/TÜRMOB API entegrasyonu değil)."""

    queryset = EInvoiceRecord.objects.select_related("client")
    serializer_class = EInvoiceRecordSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_fields = ["client", "doc_type", "direction", "status"]
    search_fields = ["client__title", "invoice_number", "counterparty_title", "counterparty_tax_number"]
    ordering_fields = ["issue_date", "amount", "created_at"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office, source=EInvoiceRecord.Source.MANUAL)
        log_action(self.request, action="create", model_name="EInvoiceRecord", object_id=instance.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request, action="update", model_name="EInvoiceRecord", object_id=instance.id)

    def perform_destroy(self, instance):
        log_action(self.request, action="delete", model_name="EInvoiceRecord", object_id=instance.id)
        instance.delete()

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """`GET .../einvoices/summary/?period_label=2026-08` -- gelen/giden
        toplam tutarları ve belge türü kırılımını döner (konsolide özet)."""
        queryset = self.get_queryset()
        period = request.query_params.get("period_label")
        if period:
            queryset = queryset.filter(period_label=period)

        incoming_total = 0
        outgoing_total = 0
        by_doc_type: dict[str, float] = {}
        for record in queryset:
            amount = float(record.amount)
            if record.direction == EInvoiceRecord.Direction.INCOMING:
                incoming_total += amount
            else:
                outgoing_total += amount
            by_doc_type[record.doc_type] = by_doc_type.get(record.doc_type, 0) + amount

        return Response({
            "incoming_total": incoming_total,
            "outgoing_total": outgoing_total,
            "net_total": outgoing_total - incoming_total,
            "count": queryset.count(),
            "by_doc_type": by_doc_type,
        })

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        """`POST .../einvoices/import-csv/` -- multipart 'file' alanıyla
        toplu e-belge kaydı içe aktarır (Luca/entegratör Excel dökümünden
        CSV'ye çevrilmiş dosya). Beklenen kolonlar:
        client_tax_number, doc_type, direction, invoice_number,
        counterparty_title, counterparty_tax_number, amount, currency,
        issue_date, period_label, status, notes
        (client_tax_number zorunlu, o vergi numarasına sahip müşteri bu
        ofiste bulunmalı)."""
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "'file' alanı ile bir CSV dosyası yükleyin."}, status=400)

        try:
            decoded = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response({"detail": "Dosya UTF-8 formatında olmalı."}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        valid_doc_types = {c for c, _ in EInvoiceRecord.DocType.choices}
        valid_directions = {c for c, _ in EInvoiceRecord.Direction.choices}
        valid_statuses = {c for c, _ in EInvoiceRecord.Status.choices}

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
                record = EInvoiceRecord.objects.create(
                    office=request.office,
                    client=client,
                    doc_type=row.get("doc_type", "e_fatura").strip() if row.get("doc_type", "").strip() in valid_doc_types else "e_fatura",
                    direction=row.get("direction", "outgoing").strip() if row.get("direction", "").strip() in valid_directions else "outgoing",
                    invoice_number=(row.get("invoice_number") or "").strip(),
                    counterparty_title=(row.get("counterparty_title") or "").strip(),
                    counterparty_tax_number=(row.get("counterparty_tax_number") or "").strip(),
                    amount=amount,
                    currency=(row.get("currency") or "TRY").strip() or "TRY",
                    issue_date=(row.get("issue_date") or "").strip() or None,
                    period_label=(row.get("period_label") or "").strip(),
                    status=row.get("status", "approved").strip() if row.get("status", "").strip() in valid_statuses else "approved",
                    notes=(row.get("notes") or "").strip(),
                    source=EInvoiceRecord.Source.CSV_IMPORT,
                )
                created.append(record.id)
            except Exception as exc:  # noqa: BLE001 -- kullanıcıya satır bazlı hata dönmek için genis yakalama
                errors.append(f"Satır {row_num}: {exc}")

        log_action(request, action="create", model_name="EInvoiceRecord",
                   metadata={"event": "csv_import", "created": len(created), "errors": len(errors)})
        return Response({"created_count": len(created), "error_count": len(errors), "errors": errors}, status=201 if created else 400)
