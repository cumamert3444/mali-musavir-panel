from django.conf import settings
from django.db import models

from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel


class ServicePackage(TenantScopedModel, TimeStampedModel):
    """Ofisin sundugu standart hizmet paketi sablonu (ornek: 'Standart
    Aylik Muhasebe', 'KDV Mukellefi Basit Paket'). Musteriye atanirken
    ucret override edilebilir (bkz. Client.monthly_fee)."""

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    default_monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["office", "name"], name="unique_service_package_per_office"),
        ]

    def __str__(self) -> str:
        return self.name


class ClientGroup(TenantScopedModel, TimeStampedModel):
    """Mukellef gruplama etiketi (rakip urunlerdeki 'mukellef gruplama'
    ozelliginin karsiligi) -- ornek: 'KDV Mukellefi', 'Buyuk Musteri',
    'Yillik Paket', 'E-Ticaret'. Serbestce tanimlanabilir, Client'a
    coktan-coga baglanir."""

    name = models.CharField(max_length=100)
    color = models.CharField(
        max_length=20, blank=True, help_text="Panelde renkli etiket icin (ornek: '#22c55e' veya 'green')."
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["office", "name"], name="unique_client_group_per_office"),
        ]

    def __str__(self) -> str:
        return self.name


class Client(TenantScopedModel, TimeStampedModel):
    """Ofisin hizmet verdigi musteri sirket/sahis (mukellef)."""

    class LegalType(models.TextChoices):
        SAHIS = "sahis", "Sahis Isletmesi"
        LTD = "ltd", "Limited Sirket"
        AS = "as", "Anonim Sirket"
        ADI_ORTAKLIK = "adi_ortaklik", "Adi Ortaklik"
        KOOPERATIF = "kooperatif", "Kooperatif"
        DERNEK_VAKIF = "dernek_vakif", "Dernek / Vakif"
        SERBEST_MESLEK = "serbest_meslek", "Serbest Meslek Erbabi"
        DIGER = "diger", "Diger"

    class Status(models.TextChoices):
        PROSPECT = "prospect", "Potansiyel Musteri"
        ACTIVE = "active", "Aktif"
        PASSIVE = "passive", "Pasif"
        FORMER = "former", "Eski Musteri"

    title = models.CharField("Unvan", max_length=255)
    legal_type = models.CharField(max_length=20, choices=LegalType.choices, default=LegalType.LTD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    tax_number = models.CharField("Vergi/TC Kimlik No", max_length=20, blank=True)
    tax_office = models.CharField("Vergi Dairesi", max_length=120, blank=True)
    mersis_no = models.CharField("Mersis No", max_length=20, blank=True)
    trade_registry_no = models.CharField("Ticaret Sicil No", max_length=30, blank=True)

    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    package = models.ForeignKey(
        ServicePackage, on_delete=models.SET_NULL, null=True, blank=True, related_name="clients"
    )
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    employee_count = models.PositiveIntegerField("Personel Sayisi", default=0, help_text="Bordro takibi icin.")
    e_invoice_enabled = models.BooleanField("e-Fatura Mukellefi", default=False)
    e_ledger_enabled = models.BooleanField("e-Defter Mukellefi", default=False)
    accounting_software = models.CharField(
        "Kullandigi Muhasebe Programi", max_length=100, blank=True,
        help_text="Ornek: Logo, Mikro, Luca, Zirve...",
    )

    start_date = models.DateField(null=True, blank=True, help_text="Ofisle calismaya baslama tarihi.")
    end_date = models.DateField(null=True, blank=True, help_text="Iliski sona erdiyse.")
    notes = models.TextField(blank=True)

    assigned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="ClientAssignment", related_name="assigned_clients"
    )
    groups = models.ManyToManyField(ClientGroup, related_name="clients", blank=True)

    class Meta:
        ordering = ["title"]
        indexes = [
            models.Index(fields=["office", "status"]),
            models.Index(fields=["office", "tax_number"]),
        ]

    def __str__(self) -> str:
        return self.title


class ClientContact(TimeStampedModel):
    """Musteri sirketteki yetkili/iletisim kisisi (ofisin direkt muhatabi)."""

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contacts")
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=100, blank=True, help_text="Ornek: Genel Mudur, Muhasebe Sorumlusu")
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "full_name"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.client.title})"


class ClientAssignment(TimeStampedModel):
    """Bir musterinin hangi ofis personeline (mali musavir/muhasebeci)
    atandigini tutan ara tablo."""

    class AssignmentRole(models.TextChoices):
        PRIMARY = "primary", "Sorumlu"
        BACKUP = "backup", "Yedek"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_assignments")
    role = models.CharField(max_length=20, choices=AssignmentRole.choices, default=AssignmentRole.PRIMARY)

    class Meta:
        unique_together = ["client", "user", "role"]

    def __str__(self) -> str:
        return f"{self.client} -> {self.user} ({self.get_role_display()})"


class Contract(TimeStampedModel):
    """Musteri ile ofis arasindaki hizmet sozlesmesi takibi (rakip
    urunlerdeki 'sozlesme-mukellef otomasyonu' ozelliginin karsiligi)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Taslak"
        ACTIVE = "active", "Yururlukte"
        EXPIRED = "expired", "Suresi Doldu"
        TERMINATED = "terminated", "Feshedildi"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="contracts")
    title = models.CharField(max_length=200, default="Hizmet Sozlesmesi")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    auto_renew = models.BooleanField(
        "Otomatik Yenilenir", default=True, help_text="Bitis tarihinde otomatik olarak yenilenir mi."
    )
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    scope_description = models.TextField(blank=True, help_text="Sozlesme kapsami: hangi hizmetler dahil.")
    file = models.FileField(upload_to="contracts/%Y/%m/", null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.title} - {self.client.title}"
