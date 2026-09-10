from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class BankStatementImport(TenantScopedModel, TimeStampedModel):
    """Bir mükellefin banka hesap ekstresinin (Excel/CSV/PDF) tek bir toplu
    içe aktarma işlemi -- yüklenen dosya + ayrıştırma sonucu burada, tek tek
    işlem satırları ise `BankTransaction` içinde tutulur.

    ÖNEMLİ -- DÜRÜST KAPSAM NOTU (bkz. apps.pos_sync.models.DailyPosReport ve
    apps.einvoices.models.EInvoiceRecord'daki benzer notlar):
    Bu panelde gerçek bir çift taraflı (double-entry) genel muhasebe defteri
    / yevmiye modülü YOKTUR ve bankaya GERÇEK ZAMANLI, OTOMATİK bir API
    bağlantısı (açık bankacılık / PSD2 benzeri) da YOKTUR. Bu modül,
    muhasebecinin bankadan indirdiği ekstre dosyasını (Excel/CSV/PDF) OKUYUP
    yapılandırılmış işlem satırlarına çevirir; muhasebeci her satıra bir
    "karşı hesap kodu" atar, sonra bu tabloyu (bkz. `export_journal` action'ı)
    kendi kullandığı muhasebe programına (Logo/Mikro/Luca vb.) elle veya
    içe aktararak işler. Yani bu, bir OCR/ayrıştırma + ön-sınıflandırma
    yardımcısıdır -- otomatik, denetlenmemiş bir muhasebe kaydı DEĞİLDİR.

    PDF ayrıştırma özellikle "en iyi çaba" (best-effort) esasına dayanır:
    banka ekstresi PDF'lerinin sayfa düzeni bankadan bankaya çok farklılık
    gösterir. Bu yüzden her içe aktarmadan sonra satırlar `BankTransaction.
    Status.DRAFT` (taslak) olarak başlar ve muhasebecinin gözden geçirip
    onaylaması beklenir; hiçbir satır otomatik olarak "onaylandı" sayılmaz.
    """

    class SourceFormat(models.TextChoices):
        EXCEL = "excel", "Excel (.xlsx)"
        CSV = "csv", "CSV"
        PDF = "pdf", "PDF"

    class Status(models.TextChoices):
        PENDING = "pending", "İşleniyor"
        PARSED = "parsed", "Ayrıştırıldı"
        PARTIAL = "partial", "Kısmen Ayrıştırıldı"
        FAILED = "failed", "Başarısız"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bank_statement_imports")

    bank_name = models.CharField("Banka", max_length=120, blank=True)
    bank_account_code = models.CharField(
        "Banka Hesap Kodu", max_length=20, blank=True,
        help_text="Tekdüzen Hesap Planı'ndaki banka hesap kodunuz, örn. 102 veya 102.01.",
    )
    account_label = models.CharField("Hesap Açıklaması", max_length=120, blank=True, help_text="Örnek: Ziraat Bankası TL Hesabı")
    period_label = models.CharField("Dönem", max_length=20, blank=True, help_text="Örnek: 2026-08")

    source_format = models.CharField(max_length=10, choices=SourceFormat.choices)
    file = models.FileField("Ekstre Dosyası", upload_to="bank_statements/%Y/%m/")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    row_count = models.PositiveIntegerField("Bulunan Satır Sayısı", default=0)
    parsed_count = models.PositiveIntegerField("Ayrıştırılan Satır Sayısı", default=0)
    error_message = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["office", "client"])]

    def __str__(self) -> str:
        return f"{self.client.title} - {self.bank_name or 'Ekstre'} ({self.period_label or self.created_at.date()})"


class BankTransaction(TenantScopedModel, TimeStampedModel):
    """Bir banka ekstresi içe aktarmasından (veya elle) gelen tek bir işlem
    satırı. `account_code` alanı muhasebecinin bu satıra atadığı KARŞI hesap
    kodudur (banka tarafı zaten `BankStatementImport.bank_account_code`'da) --
    bkz. modül docstring'i, bu gerçek bir muhasebe fişi kesme değildir,
    dışa aktarılan bir çalışma tablosudur."""

    class Direction(models.TextChoices):
        CREDIT = "credit", "Giren (Hesaba Alacak)"
        DEBIT = "debit", "Çıkan (Hesaptan Borç)"

    class Status(models.TextChoices):
        DRAFT = "draft", "Taslak — Gözden Geçirilmedi"
        MATCHED = "matched", "Hesap Kodu Atandı"
        CONFIRMED = "confirmed", "Onaylandı"

    class Source(models.TextChoices):
        IMPORT = "import", "Dosyadan İçe Aktarıldı"
        MANUAL = "manual", "Elle Girildi"

    statement = models.ForeignKey(
        BankStatementImport, on_delete=models.CASCADE, related_name="transactions", null=True, blank=True
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="bank_transactions")

    transaction_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=500, blank=True)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    account_code = models.CharField(
        "Karşı Hesap Kodu", max_length=20, blank=True,
        help_text="Örnek: 770 (Genel Yönetim Gideri), 120 (Alıcılar), 320 (Satıcılar)...",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.IMPORT)
    suggested_by_ai = models.BooleanField(
        default=False,
        help_text=(
            "Bu hesap kodu, ofisin daha önce onayladığı benzer işlemlerden "
            "ÖĞRENİLEREK otomatik önerildi mi (bkz. apps.core.account_learning) "
            "-- muhasebeci onaylayana/değiştirene kadar taslak sayılır."
        ),
    )

    raw_row_index = models.PositiveIntegerField(null=True, blank=True, help_text="Kaynak dosyadaki satır no (hata ayıklama için).")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["transaction_date", "id"]
        indexes = [
            models.Index(fields=["office", "client", "transaction_date"]),
            models.Index(fields=["office", "statement"]),
        ]

    def __str__(self) -> str:
        return f"{self.client.title} - {self.transaction_date} - {self.amount}"
