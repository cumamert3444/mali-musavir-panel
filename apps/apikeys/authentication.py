from django.conf import settings
from django.utils import timezone
from rest_framework import authentication, exceptions

from apps.apikeys.models import ApiKey

API_KEY_HEADER = "X-API-Key"


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """`X-API-Key: mmp_<prefix>_<secret>` header'i ile kimlik dogrulama.

    "API modu" burada devreye girer: settings.API_ENABLED (global anahtar)
    veya ilgili Office.api_enabled (ofis bazli anahtar) kapaliysa istek,
    anahtar gecerli olsa dahi 401 ile reddedilir.

    Basarili dogrulamada `(user, api_key)` dondurulur; `user` anahtari
    olusturan kullanicidir (audit/izin kontrollerinde kullanilir), tenant
    kimligi ise `api_key.office` uzerinden apps.core.tenant.resolve_office
    tarafindan cozulur.
    """

    keyword_header = API_KEY_HEADER

    def authenticate(self, request):
        raw_key = request.headers.get(self.keyword_header)
        if not raw_key:
            return None

        if not getattr(settings, "API_ENABLED", True):
            raise exceptions.AuthenticationFailed("API modu sistem genelinde devre disi birakilmis.")

        parsed = ApiKey.parse(raw_key)
        if parsed is None:
            raise exceptions.AuthenticationFailed("Gecersiz API anahtari formati.")
        prefix, secret = parsed

        try:
            api_key = ApiKey.objects.select_related("office", "created_by").get(prefix=prefix)
        except ApiKey.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Gecersiz API anahtari.") from exc

        if not api_key.check_secret(secret):
            raise exceptions.AuthenticationFailed("Gecersiz API anahtari.")
        if not api_key.is_active:
            raise exceptions.AuthenticationFailed("Bu API anahtari devre disi birakilmis.")
        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise exceptions.AuthenticationFailed("Bu API anahtarinin suresi dolmus.")
        if not api_key.office.api_enabled:
            raise exceptions.AuthenticationFailed("Bu ofis icin API modu aktif degil.")
        if not api_key.office.is_active:
            raise exceptions.AuthenticationFailed("Bu ofis pasif durumda.")
        if api_key.created_by is None or not api_key.created_by.is_active:
            raise exceptions.AuthenticationFailed(
                "Bu API anahtarinin sahibi kullanici artik mevcut/aktif degil; anahtar yeniden olusturulmali."
            )

        api_key.last_used_at = timezone.now()
        api_key.save(update_fields=["last_used_at"])

        return api_key.created_by, api_key

    def authenticate_header(self, request):
        return self.keyword_header
