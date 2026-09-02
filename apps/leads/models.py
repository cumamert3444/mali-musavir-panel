from django.db import models


class DemoRequest(models.Model):
    """Herkese açık pazarlama sitesindeki ('/' landing) 'Demo İsteyin' /
    iletişim formundan gelen taleplerin kaydı. Ofis (tenant) ile ilişkili
    DEĞİLDİR -- henüz kayıt olmamış potansiyel müşterilerden gelir; bu
    yüzden `TenantScopedModel`den türemez, platform genelinde tek bir
    tablodur ve Süper Admin tarafından görülür.
    """

    class Status(models.TextChoices):
        NEW = "new", "Yeni"
        CONTACTED = "contacted", "İletişime Geçildi"
        CONVERTED = "converted", "Müşteriye Dönüştü"
        DISMISSED = "dismissed", "İlgilenmiyor"

    full_name = models.CharField(max_length=150)
    office_name = models.CharField("Ofis/Firma Adı", max_length=200, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    source_path = models.CharField(max_length=200, blank=True, help_text="Formun gönderildiği sayfa (ör. /).")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email}) - {self.get_status_display()}"
