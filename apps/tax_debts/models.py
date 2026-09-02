from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class TaxDebtRecord(TenantScopedModel, TimeStampedModel):
    """Bir mükellefin vergi/SGK/diğer kurum borcu kaydı.

    Rakip ürünlerdeki (Tek Hamle) 'tek ekrandan tüm mükelleflerin vergi
    borcu & sorgulama matrisi' özelliğinin karşılığı. ÖNEMLİ: GİB/SGK'nın
    borç sorgulama sistemlerine gerçek zamanlı, resmi bir API entegrasyonu
    bu sürümde YOKTUR (bu, GİB/SGK'nın kurumsal API erişimi ve e-imza/KEP
    yetkilendirmesi gerektirir). Kayıtlar elle veya CSV toplu içe aktarma
    ile girilir; muhasebeci mükellefin borç durumunu düzenli olarak
    (e-Devlet/GİB portalından bakarak) buraya işler ve panel bunu tek bir
    konsolide matriste gösterir.
    """

    class DebtType(models.TextChoices):
        VERGI = "vergi", "Vergi (GİB)"
        SGK = "sgk", "SGK Prim Borcu"
        BELEDIYE = "belediye", "Belediye"
        DIGER = "diger", "Diğer"

    class Status(models.TextChoices):
        UNPAID = "unpaid", "Ödenmedi"
        PARTIALLY_PAID = "partially_paid", "Kısmen Ödendi"
        PAID = "paid", "Ödendi"
        DISPUTED = "disputed", "İtiraz Edildi"

    class Source(models.TextChoices):
        MANUAL = "manual", "Elle Girildi"
        CSV_IMPORT = "csv_import", "CSV İçe Aktarma"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tax_debts")

    debt_type = models.CharField(max_length=20, choices=DebtType.choices, default=DebtType.VERGI)
    period_label = models.CharField(max_length=20, blank=True, help_text="Örnek: 2026-08")
    description = models.CharField(max_length=200, blank=True, help_text="Örnek: KDV 2. Taksit, SGK Ağustos Primi")

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-due_date", "-created_at"]
        indexes = [
            models.Index(fields=["office", "status"]),
            models.Index(fields=["office", "client", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.client.title} - {self.get_debt_type_display()} - {self.amount}"
