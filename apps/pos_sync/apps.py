from django.apps import AppConfig


class PosSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pos_sync"
    verbose_name = "POS / ÖKC Gün Sonu Senkronizasyonu"
