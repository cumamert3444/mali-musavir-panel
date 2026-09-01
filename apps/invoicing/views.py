from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client
from apps.core.audit import log_action
from apps.core.tenant import office_access_allowed, resolve_office
from apps.core.views import TenantScopedViewSetMixin
from apps.invoicing.models import Payment, ServiceInvoice
from apps.invoicing.serializers import PaymentSerializer, ServiceInvoiceSerializer


class ServiceInvoiceViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = ServiceInvoice.objects.select_related("client").prefetch_related("lines", "payments")
    serializer_class = ServiceInvoiceSerializer
    filterset_fields = ["status", "client"]
    search_fields = ["invoice_number", "client__title"]
    ordering_fields = ["issue_date", "due_date"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office)
        log_action(self.request, action="create", model_name="ServiceInvoice", object_id=instance.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request, action="update", model_name="ServiceInvoice", object_id=instance.id)


class PaymentViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """`invoices/<invoice_pk>/payments/` -- bir faturaya yapilan tahsilatlar."""

    serializer_class = PaymentSerializer

    def get_invoice(self) -> ServiceInvoice:
        office = getattr(self.request, "office", None)
        if office is None:
            raise NotFound("Aktif ofis bulunamadi.")
        return get_object_or_404(ServiceInvoice, pk=self.kwargs["invoice_pk"], office=office)

    def get_queryset(self):
        return Payment.objects.filter(invoice=self.get_invoice())

    def perform_create(self, serializer):
        invoice = self.get_invoice()
        payment = serializer.save(invoice=invoice)
        self._refresh_invoice_status(invoice)
        log_action(self.request, action="create", model_name="Payment", object_id=payment.id)

    def perform_destroy(self, instance):
        invoice = instance.invoice
        instance.delete()
        self._refresh_invoice_status(invoice)

    @staticmethod
    def _refresh_invoice_status(invoice: ServiceInvoice) -> None:
        total = invoice.total_amount
        paid = invoice.paid_amount
        if total > 0 and paid >= total:
            invoice.status = ServiceInvoice.Status.PAID
        elif paid > 0:
            invoice.status = ServiceInvoice.Status.PARTIALLY_PAID
        invoice.save(update_fields=["status"])


class ClientAccountStatementView(APIView):
    """`GET /api/v1/clients/<client_pk>/account-statement/` -- cari hesap
    ekstresi (rakip urunlerdeki 'cari takip' ozelliginin karsiligi).

    Musterinin ofise olan hizmet faturasi borcu ve odemelerini kronolojik
    sirada, kosan bakiye (running balance) ile doner. Bu, gercek genel
    muhasebe defteri degil -- ofisin KENDI musteriye kestigi hizmet
    faturalari ve tahsilatlari uzerinden hesaplanan basit bir ekstredir.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, client_pk):
        # NOT: Bu duz bir APIView oldugu icin TenantScopedViewSetMixin'in
        # initial() adimi calismaz -- JWT ile gelen isteklerde middleware
        # office'i henuz cozemedigi icin burada MyOfficeView'daki gibi
        # resolve_office() ile ayrica cozmemiz gerekir.
        office = getattr(request, "office", None) or resolve_office(request)
        if office is None:
            return Response({"detail": "Aktif ofis bulunamadi."}, status=404)
        if not office_access_allowed(request, office):
            return Response({"detail": "Bu ofise erisim yetkiniz yok."}, status=403)
        client = get_object_or_404(Client, pk=client_pk, office=office)

        invoices = ServiceInvoice.objects.filter(client=client).exclude(
            status=ServiceInvoice.Status.CANCELED
        ).prefetch_related("lines", "payments")

        entries = []
        for invoice in invoices:
            entries.append({
                "date": invoice.issue_date,
                "type": "invoice",
                "reference": invoice.invoice_number,
                "description": invoice.period_label or "Hizmet faturasi",
                "debit": invoice.total_amount,
                "credit": 0,
            })
            for payment in invoice.payments.all():
                entries.append({
                    "date": payment.paid_at,
                    "type": "payment",
                    "reference": invoice.invoice_number,
                    "description": f"Tahsilat ({payment.get_method_display()})",
                    "debit": 0,
                    "credit": payment.amount,
                })

        entries.sort(key=lambda e: (e["date"], e["type"] == "payment"))

        running_balance = 0
        for entry in entries:
            running_balance += entry["debit"] - entry["credit"]
            entry["balance"] = running_balance
            entry["date"] = entry["date"].isoformat()

        total_invoiced = sum((inv.total_amount for inv in invoices), start=0)
        total_paid = sum((inv.paid_amount for inv in invoices), start=0)

        return Response({
            "client": client.id,
            "client_title": client.title,
            "entries": entries,
            "summary": {
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "balance_due": total_invoiced - total_paid,
            },
        })
