from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.models import TimeStampedModel
from apps.tenants.models import Office


class User(AbstractBaseUser, PermissionsMixin):
    """E-posta ile giris yapan custom kullanici modeli.

    Bir kullanici birden fazla ofise (Office) `Membership` uzerinden uye
    olabilir -- ayni mali musavir/muhasebeci birden fazla ofiste calisiyor
    olabilir ya da bir ofis sahibi birden fazla sube/ofis yonetebilir.
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False, help_text="Django admin paneline giris yetkisi.")
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["email"]

    def __str__(self) -> str:
        return self.get_full_name() or self.email

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self) -> str:
        return self.first_name or self.email


class Membership(TimeStampedModel):
    """Bir User'in bir Office icindeki uyeligi ve rolu."""

    class Role(models.TextChoices):
        OWNER = "owner", "Ofis Sahibi"
        ACCOUNTANT = "accountant", "Mali Musavir"
        BOOKKEEPER = "bookkeeper", "Muhasebeci"
        INTERN = "intern", "Stajyer / Yardimci Personel"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.BOOKKEEPER)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "office"]
        ordering = ["office", "role"]

    def __str__(self) -> str:
        return f"{self.user} @ {self.office} ({self.get_role_display()})"
