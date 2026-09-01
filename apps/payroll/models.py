from django.db import models

from apps.clients.models import Client
from apps.core.models import TimeStampedModel


class Employee(TimeStampedModel):
    """Bir musteri (mukellef) firmanin calisani.

    Rakip urunlerdeki (Hattat Musavir, MusavirPro+) 'SGK e-Bildirge / ise
    giris-cikis takibi' ve 'personel karti' ozelliklerinin karsiligi --
    ofisin, musterilerinin calisan sayisini ve ise giris/cikis tarihlerini
    tek yerden takip edebilmesi icin. Tenant izolasyonu `client.office`
    uzerinden dolayli saglanir (Client zaten TenantScopedModel).
    """

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Tam Zamanli"
        PART_TIME = "part_time", "Kismi Zamanli"
        INTERN = "intern", "Stajyer"
        OTHER = "other", "Diger"

    class Status(models.TextChoices):
        ACTIVE = "active", "Calisiyor"
        TERMINATED = "terminated", "Isten Ayrildi"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="employees")

    full_name = models.CharField(max_length=150)
    tc_no = models.CharField("TC Kimlik No", max_length=11, blank=True)
    sgk_sicil_no = models.CharField("SGK Sicil No", max_length=30, blank=True)
    position = models.CharField("Pozisyon/Gorev", max_length=100, blank=True)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)

    gross_salary = models.DecimalField(
        "Brut Maas", max_digits=10, decimal_places=2, null=True, blank=True
    )
    minimum_wage_support = models.BooleanField(
        "Asgari Ucret Destegi Kapsaminda", default=False,
        help_text="5510 sayili kanun kapsamindaki tesvik/destek durumu.",
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name"]
        indexes = [models.Index(fields=["client", "status"])]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.client.title})"


class PayrollRecord(TimeStampedModel):
    """Bir calisanin belirli bir donem icin bordro KAYDI.

    ONEMLI: Bu model bir HESAPLAMA MOTORU degildir -- SGK primi, gelir
    vergisi dilimleri, asgari gecim indirimi gibi degerler yil icinde
    degisen yasal parametrelere baglidir. Buradaki alanlar, ofisin kendi
    bordro yazilimi/e-Bildirge sisteminde hesapladigi NIHAI degerleri
    KAYDETMESI icindir; guncel oranlarla otomatik hesaplama SGK/GIB
    entegrasyonu tamamlandiginda ayri bir serviste ele alinmalidir (bkz.
    proje backlog'u).
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Taslak"
        CALCULATED = "calculated", "Hesaplandi"
        PAID = "paid", "Odendi"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payroll_records")
    period_label = models.CharField(max_length=20, help_text="Ornek: 2026-08")

    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sgk_employee_share = models.DecimalField("SGK Isci Payi", max_digits=10, decimal_places=2, null=True, blank=True)
    sgk_employer_share = models.DecimalField("SGK Isveren Payi", max_digits=10, decimal_places=2, null=True, blank=True)
    income_tax = models.DecimalField("Gelir Vergisi", max_digits=10, decimal_places=2, null=True, blank=True)
    stamp_tax = models.DecimalField("Damga Vergisi", max_digits=10, decimal_places=2, null=True, blank=True)
    net_salary = models.DecimalField("Net Maas", max_digits=10, decimal_places=2, null=True, blank=True)
    employer_cost = models.DecimalField(
        "Isverene Toplam Maliyet", max_digits=10, decimal_places=2, null=True, blank=True
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-period_label"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "period_label"], name="unique_payroll_record_per_period"),
        ]

    def __str__(self) -> str:
        return f"{self.employee.full_name} - {self.period_label}"
