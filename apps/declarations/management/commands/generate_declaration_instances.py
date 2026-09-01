from django.core.management.base import BaseCommand

from apps.declarations.services import generate_upcoming_declaration_instances


class Command(BaseCommand):
    help = "Aktif musteri-beyanname abonelikleri icin eksik DeclarationInstance kayitlarini uretir."

    def add_arguments(self, parser):
        parser.add_argument("--months-ahead", type=int, default=2, help="Kac ay ileriye kadar uretilecegi.")

    def handle(self, *args, **options):
        total = generate_upcoming_declaration_instances(months_ahead=options["months_ahead"])
        self.stdout.write(self.style.SUCCESS(f"{total} beyanname donemi olusturuldu/dogrulandi."))
