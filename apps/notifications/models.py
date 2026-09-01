from django.conf import settings
from django.db import models

from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class Notification(TenantScopedModel, TimeStampedModel):
    """Panel ici + (ileride) e-posta/SMS/WhatsApp bildirimleri icin ortak
    kayit. `channel` gonderim kanalini, `is_read` panel-ici okunma
    durumunu, `sent_at` disariya gercekten gonderildigi ani tutar."""

    class Channel(models.TextChoices):
        IN_APP = "in_app", "Panel Ici"
        EMAIL = "email", "E-posta"
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Category(models.TextChoices):
        DECLARATION_DUE = "declaration_due", "Beyanname Vadesi"
        INVOICE_OVERDUE = "invoice_overdue", "Gecikmis Tahsilat"
        TASK_ASSIGNED = "task_assigned", "Gorev Atamasi"
        LEGAL_NOTIFICATION = "legal_notification", "e-Tebligat / Resmi Bildirim"
        GENERAL = "general", "Genel"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)

    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)

    related_object_type = models.CharField(max_length=100, blank=True)
    related_object_id = models.CharField(max_length=64, blank=True)

    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    send_error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self) -> str:
        return f"{self.title} -> {self.recipient}"
