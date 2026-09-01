from django.conf import settings
from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class LegalNotification(TenantScopedModel, TimeStampedModel):
    """e-Tebligat / resmi bildirim takibi.

    Rakip urunlerin (ozellikle Hattat Musavir) one cikardigi 'e-Tebligat
    otomatik takip' ozelliginin karsiligi -- GIB, SGK, mahkeme/icra gibi
    kurumlardan gelen resmi tebligatlarin, cevap/itiraz suresiyle birlikte
    kaydedilip vadesi yaklastikca hatirlatildigi kayit. Gercek e-Tebligat
    sistemine (PTT/GIB) otomatik baglanti bu surumde YOK -- kayitlar simdilik
    elle veya evrak yuklemesiyle giriliyor; gercek entegrasyon backlog'da.
    """

    class Source(models.TextChoices):
        GIB = "gib", "Gelir Idaresi Baskanligi (e-Tebligat)"
        SGK = "sgk", "SGK"
        COURT_ENFORCEMENT = "court_enforcement", "Mahkeme / Icra Dairesi"
        MUNICIPALITY = "municipality", "Belediye"
        OTHER = "other", "Diger"

    class Status(models.TextChoices):
        NEW = "new", "Yeni"
        REVIEWED = "reviewed", "Incelendi"
        RESPONDED = "responded", "Cevaplandi/Islem Yapildi"
        EXPIRED = "expired", "Suresi Gecti"
        NOT_APPLICABLE = "not_applicable", "Islem Gerekmiyor"

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="legal_notifications", null=True, blank=True
    )

    source = models.CharField(max_length=30, choices=Source.choices, default=Source.GIB)
    notification_number = models.CharField("Tebligat/Ileti No", max_length=100, blank=True)
    title = models.CharField(max_length=200)
    body_summary = models.TextField(blank=True, help_text="Tebligat icerigi hakkinda kisa ozet.")

    received_at = models.DateField(help_text="Tebligatin alindigi/tebliğ edilmis sayildigi tarih.")
    response_due_date = models.DateField(
        null=True, blank=True, help_text="Cevap/itiraz icin son tarih (varsa)."
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    document = models.ForeignKey(
        "documents.Document", on_delete=models.SET_NULL, null=True, blank=True, related_name="legal_notifications"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-received_at"]
        indexes = [models.Index(fields=["office", "status", "response_due_date"])]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_source_display()})"
