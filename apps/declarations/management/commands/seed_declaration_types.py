from django.core.management.base import BaseCommand, CommandError

from apps.declarations.models import DeclarationType
from apps.tenants.models import Office

# NOT: Asagidaki vade kurallari (due_month_offset/due_day) Turkiye'de yaygin
# bilinen beyanname takvimine dayanan MAKUL VARSAYILANLARDIR. Vergi
# mevzuati siklikla degistigi icin kullanima almadan once guncel GIB/SGK
# tebligleri ile karsilastirilmali; gerekirse Django admin veya
# `/api/v1/declarations/declaration-types/` ucundan duzeltilebilir.
STANDARD_DECLARATION_TYPES = [
    {
        "code": "kdv",
        "name": "KDV Beyannamesi",
        "period": DeclarationType.Period.MONTHLY,
        "due_month_offset": 1,
        "due_day": 26,
        "description": "Aylik Katma Deger Vergisi beyannamesi.",
    },
    {
        "code": "muhtasar",
        "name": "Muhtasar ve Prim Hizmet Beyannamesi",
        "period": DeclarationType.Period.MONTHLY,
        "due_month_offset": 1,
        "due_day": 26,
        "description": "Stopaj + SGK prim bilgilerini birlestiren aylik beyanname.",
    },
    {
        "code": "gecici_vergi",
        "name": "Gecici Vergi Beyannamesi",
        "period": DeclarationType.Period.QUARTERLY,
        "due_month_offset": 2,
        "due_day": 17,
        "description": "3 aylik donemler halinde gelir/kurumlar gecici vergisi.",
    },
    {
        "code": "kurumlar_vergisi",
        "name": "Kurumlar Vergisi Beyannamesi",
        "period": DeclarationType.Period.YEARLY,
        "due_month_offset": 4,
        "due_day": 0,
        "description": "Hesap donemi sonrasi 4. ayin sonuna kadar yillik kurumlar vergisi beyani.",
    },
    {
        "code": "yillik_gelir_vergisi",
        "name": "Yillik Gelir Vergisi Beyannamesi",
        "period": DeclarationType.Period.YEARLY,
        "due_month_offset": 3,
        "due_day": 0,
        "description": "Sahis isletmeleri / serbest meslek icin yillik gelir vergisi beyani.",
    },
    {
        "code": "sgk_prim",
        "name": "SGK Aylik Prim ve Hizmet Belgesi",
        "period": DeclarationType.Period.MONTHLY,
        "due_month_offset": 1,
        "due_day": 0,
        "description": "Calisan personel icin aylik SGK prim bildirimi (Muhtasar ile birlesik olabilir).",
    },
    {
        "code": "ba_bs",
        "name": "Ba-Bs Formlari",
        "period": DeclarationType.Period.MONTHLY,
        "due_month_offset": 1,
        "due_day": 0,
        "description": "Mal ve hizmet alim/satim bildirim formlari.",
    },
    {
        "code": "damga_vergisi",
        "name": "Damga Vergisi Beyannamesi",
        "period": DeclarationType.Period.MONTHLY,
        "due_month_offset": 1,
        "due_day": 26,
        "description": "Aylik damga vergisi beyannamesi.",
    },
    {
        "code": "e_defter_berat",
        "name": "e-Defter Berat Yuklemesi",
        "period": DeclarationType.Period.MONTHLY,
        "due_month_offset": 1,
        "due_day": 0,
        "description": "Elektronik defter beratlarinin GIB'e yuklenmesi.",
    },
]


class Command(BaseCommand):
    help = "Standart beyanname turlerini bir veya tum ofisler icin olusturur (mevcut olanlari atlar)."

    def add_arguments(self, parser):
        parser.add_argument("--office-id", type=int, default=None, help="Sadece belirtilen ofis icin calistir.")
        parser.add_argument("--all", action="store_true", help="Sistemdeki tum ofisler icin calistir.")

    def handle(self, *args, **options):
        office_id = options["office_id"]
        run_all = options["all"]

        if not office_id and not run_all:
            raise CommandError("--office-id <id> ya da --all parametrelerinden birini belirtmelisiniz.")

        offices = Office.objects.filter(pk=office_id) if office_id else Office.objects.all()
        if not offices.exists():
            raise CommandError("Eslesen ofis bulunamadi.")

        total_created = 0
        for office in offices:
            created_for_office = 0
            for spec in STANDARD_DECLARATION_TYPES:
                _, created = DeclarationType.objects.get_or_create(
                    office=office,
                    code=spec["code"],
                    defaults={k: v for k, v in spec.items() if k != "code"},
                )
                created_for_office += int(created)
            total_created += created_for_office
            self.stdout.write(f"  {office.name}: {created_for_office} yeni beyanname turu olusturuldu.")

        self.stdout.write(self.style.SUCCESS(f"Tamamlandi. Toplam {total_created} kayit olusturuldu."))
