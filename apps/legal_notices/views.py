import csv
import datetime as dt
import io

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.clients.models import Client
from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.legal_notices.models import LegalNotification
from apps.legal_notices.serializers import LegalNotificationSerializer


class LegalNotificationViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """e-Tebligat / resmi bildirim takibi."""

    queryset = LegalNotification.objects.select_related("client", "assigned_to", "document")
    serializer_class = LegalNotificationSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_fields = ["status", "source", "client"]
    search_fields = ["title", "notification_number", "client__title"]
    ordering_fields = ["received_at", "response_due_date"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office)
        log_action(self.request, action="create", model_name="LegalNotification", object_id=instance.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request, action="update", model_name="LegalNotification", object_id=instance.id)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """`GET .../legal-notifications/upcoming/?days=7` -- yanit suresi
        yaklasan/gecmis tebligatlar."""
        try:
            days = int(request.query_params.get("days", 7))
        except ValueError:
            days = 7
        horizon = timezone.localdate() + dt.timedelta(days=days)
        queryset = (
            self.get_queryset()
            .filter(response_due_date__isnull=False, response_due_date__lte=horizon)
            .exclude(status__in=[LegalNotification.Status.RESPONDED, LegalNotification.Status.NOT_APPLICABLE])
            .order_by("response_due_date")
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        """`POST .../legal-notifications/import-csv/` -- toplu e-Tebligat
        kaydı içe aktarma (multipart 'file' alanı). Beklenen kolonlar:
        client_tax_number (boşsa ofis geneli), source, title, notification_number,
        received_at, response_due_date, body_summary, notes.

        NOT: GİB/SGK'nın e-Tebligat sistemine gerçek zamanlı otomatik bağlanan
        bir servis DEĞİLDİR (bkz. LegalNotification model docstring'i) --
        muhasebeci portaldan indirdiği/aldığı tebligat listesini CSV olarak
        buraya toplu yükler."""
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "'file' alanı ile bir CSV dosyası yükleyin."}, status=400)
        try:
            decoded = upload.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response({"detail": "Dosya UTF-8 formatında olmalı."}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        valid_sources = {c for c, _ in LegalNotification.Source.choices}
        clients_by_tax_no = {
            c.tax_number: c for c in Client.objects.filter(office=request.office).exclude(tax_number="")
        }

        created, errors = [], []
        for row_num, row in enumerate(reader, start=2):
            tax_no = (row.get("client_tax_number") or "").strip()
            client = clients_by_tax_no.get(tax_no) if tax_no else None
            if tax_no and not client:
                errors.append(f"Satır {row_num}: vergi no '{tax_no}' ile eşleşen müşteri bulunamadı (ofis geneli olarak eklenebilir, satırı boş bırakın).")
                continue
            title = (row.get("title") or "").strip()
            received_at = (row.get("received_at") or "").strip()
            if not title or not received_at:
                errors.append(f"Satır {row_num}: 'title' ve 'received_at' zorunludur.")
                continue
            try:
                source = row.get("source", "gib").strip() if row.get("source", "").strip() in valid_sources else "gib"
                notification = LegalNotification.objects.create(
                    office=request.office,
                    client=client,
                    source=source,
                    title=title,
                    notification_number=(row.get("notification_number") or "").strip(),
                    body_summary=(row.get("body_summary") or "").strip(),
                    received_at=received_at,
                    response_due_date=(row.get("response_due_date") or "").strip() or None,
                    notes=(row.get("notes") or "").strip(),
                )
                created.append(notification.id)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Satır {row_num}: {exc}")

        log_action(request, action="create", model_name="LegalNotification",
                   metadata={"event": "csv_import", "created": len(created), "errors": len(errors)})
        return Response({"created_count": len(created), "error_count": len(errors), "errors": errors}, status=201 if created else 400)
