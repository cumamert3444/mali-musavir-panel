"""
Aktif ofisi (tenant) bir HTTP istegi uzerinden cozumleyen ortak yardimcilar.

Bu modul hem duz Django middleware'i (apps.core.middleware.TenantMiddleware)
hem de DRF viewset mixin'i (apps.core.views.TenantScopedViewSetMixin)
tarafindan kullanilir; boylece "hangi istek hangi ofise ait" mantigi tek bir
yerde tanimli olur.

Kimlik dogrulama yontemine gore aktif ofis su oncelikle belirlenir:
1) X-API-Key ile gelen istekler  -> API anahtarinin bagli oldugu ofis.
2) Oturum acmis (JWT/session) kullanicilar -> `X-Office-Id` header'i ile
   secilen, kullanicinin uye oldugu bir ofis; header yoksa kullanicinin ilk
   (varsayilan) ofisi.
"""
from __future__ import annotations

from typing import Optional


def _get_header(request, name: str) -> Optional[str]:
    # Hem duz Django HttpRequest hem de DRF Request icin calisir.
    headers = getattr(request, "headers", None)
    if headers is not None:
        value = headers.get(name)
        if value:
            return value
    # Django'nun ham META anahtarina da bak (bazi test istemcileri icin).
    meta_key = "HTTP_" + name.upper().replace("-", "_")
    return request.META.get(meta_key) if hasattr(request, "META") else None


def resolve_office(request):
    """Istek icin aktif Office nesnesini dondurur, bulunamazsa None."""
    from apps.apikeys.models import ApiKey  # gecikmeli import: dongusel bagimliligi onler

    auth = getattr(request, "auth", None)
    if isinstance(auth, ApiKey):
        return auth.office

    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        from apps.accounts.models import Membership  # gecikmeli import

        office_id = _get_header(request, "X-Office-Id")
        qs = Membership.objects.filter(user=user, is_active=True).select_related("office")
        if office_id:
            membership = qs.filter(office_id=office_id).first()
        else:
            membership = qs.order_by("id").first()
        return membership.office if membership else None

    return None


def office_access_allowed(request, office) -> bool:
    """Cozumlenen kullanici/API anahtarinin verilen ofise gercekten erisim
    yetkisi olup olmadigini dogrular (resolve_office bulmus olsa bile,
    ekstra bir bilinc kontrolu olarak)."""
    if office is None:
        return False

    from apps.apikeys.models import ApiKey

    auth = getattr(request, "auth", None)
    if isinstance(auth, ApiKey):
        return auth.office_id == office.id and auth.is_active and office.api_enabled

    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        if getattr(user, "is_superuser", False):
            return True
        from apps.accounts.models import Membership

        return Membership.objects.filter(user=user, office=office, is_active=True).exists()

    return False
