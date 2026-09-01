from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """E-posta ile giris yapan custom User modeli icin manager (username yok)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("E-posta adresi zorunludur.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser is_staff=True olmalidir.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser is_superuser=True olmalidir.")
        return self._create_user(email, password, **extra_fields)
