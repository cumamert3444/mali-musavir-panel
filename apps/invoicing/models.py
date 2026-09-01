from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class ServiceInvoice(TenantScopedModel, TimeStampedModel):
    """Ofisin musteriye kestigi hizmet faturasi (ofisin KENDI ucreti,
    musterinin vergi beyannameleriyle karistirilmamali)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Taslak"
        SENT = "sent", "Gonderildi"
        PARTIALLY_PAID = "partially_paid", "Kismen Odendi"
        PAID = "paid", "Odendi"
        OVERDUE = "overdue", "Gecikti"
        CANCELED = "canceled", "Iptal"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=50)
    period_label = models.CharField(max_length=20, blank=True, help_text="Ornek: 2026-08 hizmet bedeli.")
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issue_date"]
        constraints = [
            models.UniqueConstraint(fields=["office", "invoice_number"], name="unique_invoice_number_per_office"),
        ]
        indexes = [models.Index(fields=["office", "status", "due_date"])]

    def __str__(self) -> str:
        return f"{self.invoice_number} - {self.client.title}"

    @property
    def total_amount(self):
        return sum((line.amount for line in self.lines.all()), start=0)

    @property
    def paid_amount(self):
        return sum((payment.amount for payment in self.payments.all()), start=0)

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(ServiceInvoice, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.description

    @property
    def amount(self):
        return self.quantity * self.unit_price


class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        BANK_TRANSFER = "bank_transfer", "Havale/EFT"
        CASH = "cash", "Nakit"
        CREDIT_CARD = "credit_card", "Kredi Karti"
        OTHER = "other", "Diger"

    invoice = models.ForeignKey(ServiceInvoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.BANK_TRANSFER)
    paid_at = models.DateField()
    reference = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-paid_at"]

    def __str__(self) -> str:
        return f"{self.invoice.invoice_number} - {self.amount}"
