from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class EInvoiceRecord(TenantScopedModel, TimeStampedModel):
    """Bir mükellefin e-Fatura/e-Arşiv/e-İrsaliye vb. GİB belge kaydı.

    ÖNEMLİ -- DÜRÜST KAPSAM NOTU:
    Bu sürümde GİB'in resmi e-Fatura/e-Arşiv sistemine (ister doğrudan GİB
    portalı, ister TÜRMOB'un ücretsiz sunduğu Luca e-Belge Portalı üzerinden)
    GERÇEK ZAMANLI, OTOMATİK bir API entegrasyonu YOKTUR. Bunun nedeni:
      - TÜRMOB Luca e-Belge Portalı (turmobefatura.luca.com.tr) bir insanın
        tarayıcıdan kullanıcı adı/şifre ile giriş yaptığı bir web portalıdır;
        üçüncü parti yazılımların bağlanabileceği genel/dokümante bir REST
        veya SOAP API'si kamuya açık değildir. TÜRMOB'un e-Birlik üzerinden
        verdiği "servis anahtarı" esas olarak Luca'nın KENDİ ürünlerini
        (Luca Net, MMP vb.) birbirine bağlamak ve VKN/TCKN sorgulamak
        içindir -- dışarıdan bir SaaS panelinin bunu kullanarak fatura
        gönderip alması için resmi/genel bir yol yoktur.
      - Foriba/Uyumsoft/QNB eFinans gibi özel entegratörlerin gerçek API
        erişimi (bayilik sözleşmesi + kimlik bilgileri) bu ofiste henüz
        yoktur.
    Bu yüzden kayıtlar, muhasebecinin Luca portalından (veya kullandığı
    entegratörden) aldığı fatura listesi Excel/CSV dökümünü buraya toplu
    içe aktarmasıyla (ya da elle) oluşturulur; panel bunları tek bir
    konsolide, filtrelenebilir görünümde sunar. `source` alanı kaydın nasıl
    geldiğini belirtir. İleride gerçek bir API erişimi (TÜRMOB servis
    anahtarı, Foriba/Uyumsoft/QNB eFinans bayiliği vb.) edinilirse, bu CSV
    içe aktarma action'ının yerini `apps.einvoices.views` içinde aynı
    ViewSet üzerinde yeni bir `sync` action'ı alabilir -- veri modeli ve
    frontend zaten buna hazır (bkz. `source` choices'a `SYNC` eklenebilir).
    """

    class DocType(models.TextChoices):
        E_FATURA = "e_fatura", "e-Fatura"
        E_ARSIV = "e_arsiv", "e-Arşiv Fatura"
        E_IRSALIYE = "e_irsaliye", "e-İrsaliye"
        E_MM = "e_mm", "e-Müstahsil Makbuzu"
        E_SMM = "e_smm", "e-Serbest Meslek Makbuzu"

    class Direction(models.TextChoices):
        INCOMING = "incoming", "Gelen (Alış)"
        OUTGOING = "outgoing", "Giden (Satış)"

    class Status(models.TextChoices):
        APPROVED = "approved", "Onaylandı"
        PENDING = "pending", "Beklemede"
        REJECTED = "rejected", "Reddedildi"
        CANCELLED = "cancelled", "İptal Edildi"

    class Source(models.TextChoices):
        MANUAL = "manual", "Elle Girildi"
        CSV_IMPORT = "csv_import", "CSV/Excel İçe Aktarma"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="einvoices")

    doc_type = models.CharField(max_length=20, choices=DocType.choices, default=DocType.E_FATURA)
    direction = models.CharField(max_length=10, choices=Direction.choices, default=Direction.OUTGOING)

    invoice_number = models.CharField(
        max_length=60, blank=True, help_text="Fatura no / ETTN (GİB UUID)."
    )
    counterparty_title = models.CharField(
        max_length=200, blank=True, help_text="Karşı taraf (gelen faturada satıcı, giden faturada alıcı) unvanı."
    )
    counterparty_tax_number = models.CharField(max_length=20, blank=True)

    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=6, default="TRY")
    issue_date = models.DateField(null=True, blank=True)
    period_label = models.CharField(max_length=20, blank=True, help_text="Örnek: 2026-08")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPROVED)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issue_date", "-created_at"]
        indexes = [
            models.Index(fields=["office", "client", "direction"]),
            models.Index(fields=["office", "doc_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.client.title} - {self.get_doc_type_display()} - {self.invoice_number or self.amount}"
