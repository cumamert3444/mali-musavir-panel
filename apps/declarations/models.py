from django.conf import settings
from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class DeclarationType(TenantScopedModel, TimeStampedModel):
    """Bir beyanname/bildirge turu ve vade hesaplama kurali.

    Vade, `period_end` (donem sonu) tarihine `due_month_offset` ay eklenip
    gunu `due_day`e (0 = ayin son gunu) sabitlenerek hesaplanir. Bu kurallar
    ofis bazinda ozellestirilebilir cunku mevzuat degisebilir; seed komutu
    (`seed_declaration_types`) makul varsayilanlarla baslangic verisi
    olusturur -- **guncel resmi vade tarihleri ile karsilastirilmalidir.**
    """

    class Period(models.TextChoices):
        MONTHLY = "monthly", "Aylik"
        QUARTERLY = "quarterly", "3 Aylik (Ceyrek)"
        YEARLY = "yearly", "Yillik"

    code = models.SlugField(max_length=50)
    name = models.CharField(max_length=150)
    period = models.CharField(max_length=20, choices=Period.choices, default=Period.MONTHLY)
    due_month_offset = models.PositiveSmallIntegerField(
        default=1, help_text="Donem bitiminden kac ay sonra beyan edilir."
    )
    due_day = models.PositiveSmallIntegerField(
        default=26, help_text="Vade gunu (1-31). 0 = o ayin son gunu."
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["office", "code"], name="unique_declaration_type_per_office"),
        ]

    def __str__(self) -> str:
        return self.name


class ClientDeclarationSubscription(TimeStampedModel):
    """Bir musterinin hangi beyanname turlerine tabi oldugu (ornek: KDV
    mukellefi olmayan bir musteri icin KDV beyannamesi uretilmez)."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="declaration_subscriptions")
    declaration_type = models.ForeignKey(DeclarationType, on_delete=models.CASCADE, related_name="subscriptions")
    is_active = models.BooleanField(default=True)
    starts_on = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ["client", "declaration_type"]

    def __str__(self) -> str:
        return f"{self.client} - {self.declaration_type}"


class DeclarationInstance(TenantScopedModel, TimeStampedModel):
    """Bir musterinin belirli bir donem icin somut beyanname kaydi."""

    class Status(models.TextChoices):
        PENDING = "pending", "Bekliyor"
        IN_PROGRESS = "in_progress", "Hazirlaniyor"
        SUBMITTED = "submitted", "Beyan Edildi"
        PAID = "paid", "Odendi/Kapandi"
        OVERDUE = "overdue", "Gecikti"
        NOT_APPLICABLE = "not_applicable", "Bu Donem Gecerli Degil"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="declaration_instances")
    declaration_type = models.ForeignKey(DeclarationType, on_delete=models.PROTECT, related_name="instances")

    period_label = models.CharField(max_length=20, help_text="Ornek: 2026-08, 2026-Q3, 2026")
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    # Beyan edilen gercek rakamlar -- Hattat/Tek Hamle tarzi "beyanname
    # capraz esleme / risk motoru" bu alanlar uzerinden calisir (bkz.
    # apps.declarations.risk_engine). Ornekler: KDV'de beyan edilen matrah,
    # Muhtasar'da bildirilen ucret/stopaj matrahi. Gercek GIB entegrasyonu
    # olmadigindan bu degerler muhasebeci tarafindan beyanname
    # onaylandiginda elle girilir.
    declared_amount = models.DecimalField(
        "Beyan Edilen Matrah/Tutar", max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Ornek: KDV matrahi, Muhtasar'da bildirilen brut ucret toplami.",
    )
    declared_tax_amount = models.DecimalField(
        "Hesaplanan/Odenecek Vergi Tutari", max_digits=14, decimal_places=2, null=True, blank=True,
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["due_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["client", "declaration_type", "period_start"], name="unique_instance_per_period"
            ),
        ]
        indexes = [
            models.Index(fields=["office", "due_date", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.client} - {self.declaration_type} - {self.period_label}"

    @property
    def is_overdue(self) -> bool:
        from django.utils import timezone

        return self.status in {self.Status.PENDING, self.Status.IN_PROGRESS} and self.due_date < timezone.localdate()
