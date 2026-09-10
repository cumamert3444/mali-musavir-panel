import uuid

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """created_at/updated_at alanlarini standartlastiran soyut model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """
    Onemli islemler (olusturma/guncelleme/silme, giris denemeleri, API key
    kullanimi vb.) icin degismez denetim kaydi.

    Not: Bu tablo bilerek TenantScopedModel'den turemez; super admin tum
    ofislerin loglarini gorebilmeli. `office` alani nullable tutulur (ornegin
    ofis-oncesi kayit / login denemesi gibi olaylar icin).
    """

    class Action(models.TextChoices):
        CREATE = "create", "Olusturuldu"
        UPDATE = "update", "Guncellendi"
        DELETE = "delete", "Silindi"
        LOGIN = "login", "Giris yapildi"
        LOGIN_FAILED = "login_failed", "Basarisiz giris"
        API_ACCESS = "api_access", "API erisimi"
        OTHER = "other", "Diger"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    office = models.ForeignKey(
        "tenants.Office", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs"
    )
    actor_label = models.CharField(
        max_length=150, blank=True, help_text="Kullanici silinmis olsa bile kim oldugunu hatirlamak icin."
    )
    action = models.CharField(max_length=20, choices=Action.choices, default=Action.OTHER)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["office", "created_at"]),
            models.Index(fields=["model_name", "object_id"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - basit temsil
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.actor_label or 'sistem'} - {self.get_action_display()}"


class AccountCodeMemory(models.Model):
    """Ofis bazında ÖĞRENİLMİŞ "açıklama/karşı taraf deseni -> hesap kodu"
    eşleşmeleri -- banka ekstresi işleme ve e-Fatura modüllerindeki "hesap
    kodu öner" özelliğinin belleği.

    ÖNEMLİ -- DÜRÜST KAPSAM NOTU: Bu bir büyük dil modeli (LLM/"yapay zeka")
    DEĞİLDİR; Anthropic/Claude, OpenAI, Groq gibi hiçbir dış AI sağlayıcısına
    bağlanmaz, API anahtarı gerektirmez, ücretsizdir ve internet erişimi
    olmayan bir ortamda bile çalışır. Basit ama etkili bir "öğrenen kural
    motoru"dur: muhasebeci bir işleme hesap kodu ATADIĞINDA/ONAYLADIĞINDA
    (bkz. apps.core.account_learning.learn_mapping), bu eşleşme burada
    birikir (`hit_count` artar); yeni bir kayıt geldiğinde (bkz. `suggest`)
    aynı desen için en çok kullanılan hesap kodu ÖNERİ olarak sunulur --
    otomatik/kesin bir atama değildir, muhasebeci her zaman değiştirebilir
    ve öneriyi görmezden gelebilir. Öneriler kendi kendini beslemez: sadece
    insanın onayladığı/girdiği kodlar öğrenilir, sistemin kendi önerileri
    tekrar öğrenme verisine dönmez -- bu, yanlış bir önerinin kendini
    büyütmesini engeller.
    """

    office = models.ForeignKey(
        "tenants.Office", on_delete=models.CASCADE, related_name="account_code_memories"
    )
    source_app = models.CharField(
        max_length=20,
        choices=[("bank_statement", "Banka Ekstresi"), ("einvoice", "e-Fatura")],
    )
    match_key = models.CharField(
        max_length=255, help_text="Normalize edilmiş açıklama/karşı taraf deseni."
    )
    account_code = models.CharField(max_length=20)
    hit_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-hit_count", "-last_used_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["office", "source_app", "match_key", "account_code"],
                name="unique_account_code_memory_entry",
            )
        ]
        indexes = [
            models.Index(fields=["office", "source_app", "match_key"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.source_app}: {self.match_key} -> {self.account_code} ({self.hit_count}x)"
