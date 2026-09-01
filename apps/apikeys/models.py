import hashlib
import secrets

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.tenants.models import Office

KEY_PREFIX_LENGTH = 10
KEY_SECRET_LENGTH = 43  # secrets.token_urlsafe(32) -> ~43 karakter


def _hash_secret(secret: str) -> str:
    # API anahtarlarinin entropisi zaten cok yuksek (256 bit) oldugundan,
    # her istekte hizli dogrulanabilmesi icin yavas bir sifre hash'i (PBKDF2
    # vb.) yerine tuzsuz SHA-256 kullaniliyor -- GitHub/Stripe PAT'lerinde
    # kullanilan yaklasimin ayni. Ham anahtar hicbir zaman saklanmaz.
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class ApiKey(TimeStampedModel):
    """Tenant basina dis sistem entegrasyonlari (e-Fatura/e-Defter koprusu,
    muhasebe programi, mobil uygulama, vb.) icin API anahtari.

    Ham anahtar SADECE olusturulma aninda donulur; sonrasinda yalnizca
    `prefix` (tanima icin) ve `hashed_key` (dogrulama icin) saklanir.
    """

    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name="api_keys")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    name = models.CharField(max_length=100, help_text="Bu anahtarin ne icin kullanildigini hatirlatan etiket.")
    prefix = models.CharField(max_length=KEY_PREFIX_LENGTH, unique=True, editable=False)
    hashed_key = models.CharField(max_length=64, editable=False)
    scopes = models.JSONField(default=list, blank=True, help_text="Ileride ince taneli yetkilendirme icin.")
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.prefix}...) - {self.office}"

    @classmethod
    def generate(cls, *, office: Office, name: str, created_by=None) -> tuple["ApiKey", str]:
        """Yeni bir API anahtari olusturur ve (nesne, ham_anahtar) dondurur.
        Ham anahtar sadece bu cagrida gorunur, tekrar gosterilemez."""
        prefix = secrets.token_hex(KEY_PREFIX_LENGTH // 2)
        secret = secrets.token_urlsafe(32)
        raw_key = f"mmp_{prefix}_{secret}"

        instance = cls.objects.create(
            office=office,
            created_by=created_by,
            name=name,
            prefix=prefix,
            hashed_key=_hash_secret(secret),
        )
        return instance, raw_key

    @staticmethod
    def parse(raw_key: str) -> tuple[str, str] | None:
        """`mmp_<prefix>_<secret>` formatindaki anahtardan (prefix, secret)
        cikarir; format uymuyorsa None doner."""
        parts = raw_key.split("_", 2)
        if len(parts) != 3 or parts[0] != "mmp":
            return None
        return parts[1], parts[2]

    def check_secret(self, secret: str) -> bool:
        return secrets.compare_digest(self.hashed_key, _hash_secret(secret))
