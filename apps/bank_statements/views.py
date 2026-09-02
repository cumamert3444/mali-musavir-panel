import csv
import io

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.bank_statements.models import BankStatementImport, BankTransaction
from apps.bank_statements.serializers import (
    BankStatementImportListSerializer,
    BankStatementImportSerializer,
    BankTransactionSerializer,
)
from apps.bank_statements.services import parse_statement_file
from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin


class BankStatementImportViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Banka ekstresi içe aktarma işlemleri -- bkz.
    apps.bank_statements.models.BankStatementImport docstring'i (dürüst
    kapsam notu: gerçek bankacılık API'si değil, dosya ayrıştırma).

    Bir kayıt oluşturulduğunda (`perform_create`) dosya hemen ayrıştırılır
    ve satırlar `BankTransaction.Status.DRAFT` olarak oluşturulur --
    muhasebecinin gözden geçirip hesap kodu ataması beklenir."""

    queryset = BankStatementImport.objects.select_related("client").prefetch_related("transactions")
    serializer_class = BankStatementImportSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_fields = ["client", "status", "source_format"]
    search_fields = ["client__title", "bank_name", "period_label"]
    ordering_fields = ["created_at", "period_label"]

    def get_serializer_class(self):
        if self.action == "list":
            return BankStatementImportListSerializer
        return BankStatementImportSerializer

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office)
        log_action(self.request, action="create", model_name="BankStatementImport", object_id=instance.id,
                   metadata={"event": "upload", "source_format": instance.source_format})
        self._parse(instance)

    def perform_destroy(self, instance):
        log_action(self.request, action="delete", model_name="BankStatementImport", object_id=instance.id)
        instance.delete()

    def _parse(self, instance: BankStatementImport) -> None:
        """Dosyayi ayristirip BankTransaction satirlari olusturur; sonucu
        instance uzerinde (status/row_count/parsed_count/error_message)
        gunceller. Import-kaynakli mevcut satirlar once silinir (reparse
        senaryosu icin), elle girilmis (source=manual) satirlara dokunulmaz."""
        instance.transactions.filter(source=BankTransaction.Source.IMPORT).delete()

        try:
            instance.file.open("rb")
            rows, errors = parse_statement_file(instance.source_format, instance.file)
        except Exception as exc:  # noqa: BLE001 -- ayristirma hatasi tum istegi dusurmesin
            instance.status = BankStatementImport.Status.FAILED
            instance.error_message = f"Dosya açılamadı: {exc}"
            instance.row_count = 0
            instance.parsed_count = 0
            instance.save(update_fields=["status", "error_message", "row_count", "parsed_count", "updated_at"])
            return
        finally:
            try:
                instance.file.close()
            except Exception:  # noqa: BLE001
                pass

        created = 0
        for row in rows:
            try:
                BankTransaction.objects.create(
                    office=instance.office,
                    statement=instance,
                    client=instance.client,
                    transaction_date=row.get("transaction_date"),
                    description=row.get("description") or "",
                    direction=row.get("direction") or BankTransaction.Direction.DEBIT,
                    amount=row.get("amount") or 0,
                    balance_after=row.get("balance_after"),
                    raw_row_index=row.get("raw_row_index"),
                    source=BankTransaction.Source.IMPORT,
                    status=BankTransaction.Status.DRAFT,
                )
                created += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Satır {row.get('raw_row_index')}: kayıt oluşturulamadı ({exc})")

        instance.row_count = created + len(errors)
        instance.parsed_count = created
        instance.error_message = "\n".join(errors[:200])
        if created == 0:
            instance.status = BankStatementImport.Status.FAILED
        elif errors:
            instance.status = BankStatementImport.Status.PARTIAL
        else:
            instance.status = BankStatementImport.Status.PARSED
        instance.save(update_fields=["status", "row_count", "parsed_count", "error_message", "updated_at"])

    @action(detail=True, methods=["post"])
    def reparse(self, request, pk=None):
        """`POST .../bank-statements/{id}/reparse/` -- dosyayı yeniden
        ayrıştırır (ör. parser iyileştirildikten sonra); elle eklenmiş
        satırlar korunur, dosyadan gelen satırlar yeniden oluşturulur."""
        instance = self.get_object()
        self._parse(instance)
        log_action(request, action="update", model_name="BankStatementImport", object_id=instance.id,
                   metadata={"event": "reparse"})
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["get"], url_path="export-journal")
    def export_journal(self, request, pk=None):
        """`GET .../bank-statements/{id}/export-journal/` -- muhasebecinin
        kendi muhasebe programına (Logo/Mikro/Luca vb.) elle veya içe
        aktararak yükleyebileceği bir "muhasebe fişi taslağı" CSV'si
        döner. Bu GERÇEK bir muhasebe fişi kesme işlemi DEĞİLDİR --
        bkz. modül docstring'i."""
        instance = self.get_object()
        buffer = io.StringIO()
        buffer.write("﻿")  # Excel'de Türkçe karakterlerin doğru görünmesi için BOM
        writer = csv.writer(buffer, delimiter=";")
        writer.writerow([
            "Tarih", "Açıklama", "Banka Hesap Kodu", "Karşı Hesap Kodu",
            "Borç Tutarı", "Alacak Tutarı", "Durum", "Bakiye",
        ])
        for tx in instance.transactions.all().order_by("transaction_date", "id"):
            is_debit = tx.direction == BankTransaction.Direction.DEBIT
            writer.writerow([
                tx.transaction_date.isoformat() if tx.transaction_date else "",
                tx.description,
                instance.bank_account_code,
                tx.account_code,
                f"{tx.amount}" if is_debit else "",
                f"{tx.amount}" if not is_debit else "",
                tx.get_status_display(),
                tx.balance_after if tx.balance_after is not None else "",
            ])

        log_action(request, action="other", model_name="BankStatementImport", object_id=instance.id,
                   metadata={"event": "export_journal"})
        response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
        filename = f"muhasebe-fisi-{instance.client_id}-{instance.period_label or instance.id}.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class BankTransactionViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Tekil banka işlem satırları -- ekstre içe aktarımından gelen
    satırların hesap kodu atanması/düzeltilmesi ve elle işlem eklenmesi
    için kullanılır."""

    queryset = BankTransaction.objects.select_related("client", "statement")
    serializer_class = BankTransactionSerializer
    filterset_fields = ["client", "statement", "status", "direction", "source"]
    search_fields = ["description", "account_code"]
    ordering_fields = ["transaction_date", "amount", "created_at"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office, source=BankTransaction.Source.MANUAL)
        log_action(self.request, action="create", model_name="BankTransaction", object_id=instance.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request, action="update", model_name="BankTransaction", object_id=instance.id)

    def perform_destroy(self, instance):
        log_action(self.request, action="delete", model_name="BankTransaction", object_id=instance.id)
        instance.delete()
