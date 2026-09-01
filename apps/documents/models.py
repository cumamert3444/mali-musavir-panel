from django.conf import settings
from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel
from apps.declarations.models import DeclarationInstance


def client_document_upload_path(instance: "Document", filename: str) -> str:
    return f"offices/{instance.office_id}/clients/{instance.client_id or 'genel'}/{filename}"


class DocumentCategory(TenantScopedModel, TimeStampedModel):
    """Ornek: Fatura, Fis, Dekont, Sozlesme, Beyanname Ciktisi, Kimlik/Imza Sirkuleri."""

    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Document categories"
        constraints = [
            models.UniqueConstraint(fields=["office", "name"], name="unique_document_category_per_office"),
        ]

    def __str__(self) -> str:
        return self.name


class Document(TenantScopedModel, TimeStampedModel):
    """Yuklenen bir evrak. `client` bos birakilirsa ofis geneline ait bir
    belge (ornek: ofisin kendi sozlesme sablonu) olarak degerlendirilir."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="documents", null=True, blank=True)
    category = models.ForeignKey(
        DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents"
    )
    declaration_instance = models.ForeignKey(
        DeclarationInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents"
    )

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=client_document_upload_path)
    description = models.TextField(blank=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["office", "client"])]

    def __str__(self) -> str:
        return self.title
