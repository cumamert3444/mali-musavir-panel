"""Platform Süper Admin kullanıcısını (SaaS sahibi) oluşturur/günceller.

İdempotenttir -- her `preDeployCommand` çalıştığında (her deploy'da) tekrar
çağrılsa bile hata vermez; kullanıcı zaten varsa sadece yetki bayraklarının
(is_staff/is_superuser) açık olduğundan emin olur ve şifreyi DEĞİŞTİRMEZ
(kullanıcı ilk girişten sonra şifresini değiştirmiş olabilir).

Süper admin, herhangi bir ofise (tenant) üye DEĞİLDİR -- platform genelinde
`/api/v1/tenants/admin/...` uç noktalarına `IsAdminUser`/`is_superuser`
kontrolüyle erişir (bkz. apps.tenants.views, apps.core.permissions).
"""
from django.core.management.base import BaseCommand

from apps.accounts.models import User

DEFAULT_EMAIL = "cumamert3444@gmail.com"
DEFAULT_PASSWORD = "Admin2026!"


class Command(BaseCommand):
    help = "Platform süper admin kullanıcısını oluşturur (yoksa) ve is_staff/is_superuser bayraklarını garanti eder."

    def add_arguments(self, parser):
        parser.add_argument("--email", default=DEFAULT_EMAIL)
        parser.add_argument("--password", default=DEFAULT_PASSWORD)

    def handle(self, *args, **options):
        email = options["email"].lower().strip()
        password = options["password"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={"first_name": "Süper", "last_name": "Admin", "is_staff": True, "is_superuser": True},
        )

        changed_fields = []
        if not user.is_staff:
            user.is_staff = True
            changed_fields.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            changed_fields.append("is_superuser")
        if not user.is_active:
            user.is_active = True
            changed_fields.append("is_active")

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Süper admin oluşturuldu: {email} / {password}  (İLK GİRİŞTEN SONRA ŞİFRENİZİ DEĞİŞTİRİN.)"
            ))
        elif changed_fields:
            user.save(update_fields=changed_fields)
            self.stdout.write(self.style.SUCCESS(
                f"Süper admin zaten vardı ({email}); eksik yetkiler tamamlandı: {', '.join(changed_fields)}."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f"Süper admin zaten mevcut ve yetkileri doğru: {email}."))
