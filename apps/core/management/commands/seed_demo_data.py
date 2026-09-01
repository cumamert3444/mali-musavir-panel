import datetime as dt

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.accounts.models import Membership, User
from apps.clients.models import Client, ServicePackage
from apps.declarations.models import ClientDeclarationSubscription, DeclarationType
from apps.declarations.services import generate_upcoming_declaration_instances
from apps.tenants.models import Office, Subscription, SubscriptionPlan


class Command(BaseCommand):
    help = (
        "Hizli deneme icin ornek bir ofis, sahip kullanici, birkac musteri ve "
        "beyanname takvimi olusturur. SADECE gelistirme ortaminda kullanin."
    )

    def add_arguments(self, parser):
        parser.add_argument("--email", default="demo@ofis.test")
        parser.add_argument("--password", default="demo12345")

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]

        office, _ = Office.objects.get_or_create(
            name="Demo Mali Musavirlik",
            defaults={"tax_number": "1234567890", "api_enabled": True},
        )

        plan, _ = SubscriptionPlan.objects.get_or_create(
            code="demo", defaults={"name": "Demo Paketi", "max_users": 5, "max_clients": 100}
        )
        Subscription.objects.get_or_create(office=office, defaults={"plan": plan, "status": "active"})

        owner, created = User.objects.get_or_create(email=email, defaults={"first_name": "Demo", "last_name": "Sahip"})
        if created:
            owner.set_password(password)
            owner.save()
        Membership.objects.get_or_create(user=owner, office=office, defaults={"role": Membership.Role.OWNER})

        package, _ = ServicePackage.objects.get_or_create(
            office=office, name="Standart Aylik Muhasebe", defaults={"default_monthly_fee": 5000}
        )

        demo_clients = [
            {"title": "ABC Insaat Ltd. Sti.", "legal_type": Client.LegalType.LTD, "tax_number": "1111111111"},
            {"title": "Ayse Yilmaz - Serbest Muhasebeci", "legal_type": Client.LegalType.SERBEST_MESLEK,
             "tax_number": "22222222222"},
            {"title": "Mavi Tekstil A.S.", "legal_type": Client.LegalType.AS, "tax_number": "3333333333"},
        ]
        clients = []
        for spec in demo_clients:
            client, _ = Client.objects.get_or_create(
                office=office,
                title=spec["title"],
                defaults={
                    "legal_type": spec["legal_type"],
                    "tax_number": spec["tax_number"],
                    "package": package,
                    "monthly_fee": package.default_monthly_fee,
                    "start_date": dt.date.today() - dt.timedelta(days=180),
                },
            )
            clients.append(client)

        call_command("seed_declaration_types", office_id=office.id)

        kdv = DeclarationType.objects.get(office=office, code="kdv")
        muhtasar = DeclarationType.objects.get(office=office, code="muhtasar")
        for client in clients:
            ClientDeclarationSubscription.objects.get_or_create(client=client, declaration_type=kdv)
            ClientDeclarationSubscription.objects.get_or_create(client=client, declaration_type=muhtasar)

        created_count = generate_upcoming_declaration_instances(months_ahead=2)

        self.stdout.write(self.style.SUCCESS(
            f"Demo veri hazir. Giris: {email} / {password}  |  Ofis: {office.name}  |  "
            f"{len(clients)} musteri, {created_count} beyanname donemi olusturuldu."
        ))
