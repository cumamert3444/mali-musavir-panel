from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class DailyPosReport(TenantScopedModel, TimeStampedModel):
    """Bir mükellefin bir güne ait POS/ÖKC (Ödeme Kaydedici Cihaz) gün sonu
    (Z raporu) özeti.

    Rakip ürünlerdeki 'banka POS + ÖKC gün sonu raporu senkronizasyonu'
    özelliğinin karşılığı. Alanlar, Tekdüzen Hesap Planı'ndaki ilgili
    hesap gruplarına KAVRAMSAL olarak karşılık gelir:
      - `pos_collection`  -> 108 Diğer Hazır Değerler (banka/POS tahsilatı)
      - `gross_sales`     -> 600 Yurtiçi Satışlar (KDV hariç net satış)
      - `vat_amount`      -> 391 Hesaplanan KDV

    ÖNEMLİ - dürüst kapsam sınırı: Bu, gerçek bir çift taraflı (double-entry)
    muhasebe defteri / otomatik fiş kesme motoru DEĞİLDİR -- panelde genel
    muhasebe (yevmiye/defter-i kebir) modülü yoktur. Bu model sadece,
    banka/ÖKC gün sonu raporlarından elle veya CSV toplu içe aktarma ile
    girilen özet rakamları saklar; muhasebeci bu rakamları kendi muhasebe
    yazılımına (Logo/Mikro/Luca) ayrıca işler.
    """

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="pos_reports")

    report_date = models.DateField()
    okc_no = models.CharField("ÖKC Cihaz No", max_length=50, blank=True)

    gross_sales = models.DecimalField("Net Satış (600)", max_digits=14, decimal_places=2, default=0)
    vat_amount = models.DecimalField("Hesaplanan KDV (391)", max_digits=14, decimal_places=2, default=0)
    pos_collection = models.DecimalField("POS Tahsilatı (108)", max_digits=14, decimal_places=2, default=0)
    cash_collection = models.DecimalField("Nakit Tahsilat", max_digits=14, decimal_places=2, default=0)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-report_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "report_date", "okc_no"], name="unique_pos_report_per_client_day_device"
            ),
        ]
        indexes = [models.Index(fields=["office", "client", "report_date"])]

    def __str__(self) -> str:
        return f"{self.client.title} - {self.report_date}"

    @property
    def total_sales_incl_vat(self):
        return self.gross_sales + self.vat_amount
