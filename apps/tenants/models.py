from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel


class Office(TimeStampedModel):
    """Bir mali musavirlik ofisi = bir tenant (kiraci).

    Sistemdeki hemen her sey (musteri, beyanname, evrak, gorev, fatura...)
    dogrudan ya da dolayli olarak bir Office'e baglidir.
    """

    name = models.CharField("Ofis adi", max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    legal_name = models.CharField("Unvan", max_length=255, blank=True)
    tax_number = models.CharField("Vergi No", max_length=20, blank=True)
    tax_office = models.CharField("Vergi Dairesi", max_length=120, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)

    # API modu: bu ofis icin dis sistem entegrasyonlarina (X-API-Key ile
    # gelen istekler) izin verilip verilmedigi. Global anahtar
    # settings.API_ENABLED ile birlikte degerlendirilir (bkz.
    # apps.apikeys.authentication.ApiKeyAuthentication).
    api_enabled = models.BooleanField(
        "API modu aktif mi", default=False, help_text="Kapaliysa bu ofis icin X-API-Key ile erisim reddedilir."
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:200] or "ofis"
            slug = base_slug
            counter = 1
            while Office.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)


class SubscriptionPlan(TimeStampedModel):
    """SaaS abonelik paketi tanimi (Baslangic/Profesyonel/Kurumsal gibi)."""

    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    max_users = models.PositiveIntegerField(default=3)
    max_clients = models.PositiveIntegerField(default=50)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    api_access_included = models.BooleanField(default=False)
    features = models.JSONField(default=list, blank=True, help_text="Serbest metin ozellik listesi.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price_monthly"]

    def __str__(self) -> str:
        return self.name


class Subscription(TimeStampedModel):
    class Status(models.TextChoices):
        TRIALING = "trialing", "Deneme"
        ACTIVE = "active", "Aktif"
        PAST_DUE = "past_due", "Odeme Gecikti"
        CANCELED = "canceled", "Iptal Edildi"

    office = models.OneToOneField(Office, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIALING)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.office.name} - {self.plan.name} ({self.get_status_display()})"
