"""
Ana URL yapilandirmasi.

API modu / Swagger:
- /api/v1/schema/        -> OpenAPI 3 semasi (JSON)
- /api/v1/docs/          -> Swagger UI (interaktif, tarayicidan denenebilir)
- /api/v1/redoc/         -> ReDoc (salt okunur, daha temiz dokumantasyon)

Kimlik dogrulama:
- /api/v1/auth/token/            -> email+sifre ile JWT al (login)
- /api/v1/auth/token/refresh/    -> refresh token ile yeni access token
- /api/v1/auth/token/verify/     -> bir token'in gecerliligini dogrula
- X-API-Key header'i ile de kimlik dogrulanabilir (bkz. apps.apikeys) --
  bunun icin ofis ayarlarindan API modunun acik olmasi gerekir.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from apps.core.site_views import robots_txt, sitemap_xml, spa_view, status_check

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Kimlik dogrulama -------------------------------------------------
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/v1/auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),

    # --- API modu / OpenAPI dokumantasyonu ---------------------------------
    path("api/v1/status/", status_check, name="status-check"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # --- Uygulama modulleri --------------------------------------------------
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/tenants/", include("apps.tenants.urls")),
    path("api/v1/apikeys/", include("apps.apikeys.urls")),
    path("api/v1/", include("apps.clients.urls")),
    path("api/v1/", include("apps.declarations.urls")),
    path("api/v1/", include("apps.documents.urls")),
    path("api/v1/", include("apps.tasks.urls")),
    path("api/v1/", include("apps.invoicing.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.payroll.urls")),
    path("api/v1/", include("apps.legal_notices.urls")),
    path("api/v1/", include("apps.tax_debts.urls")),
    path("api/v1/", include("apps.pos_sync.urls")),
    path("api/v1/", include("apps.leads.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# --- SEO: robots.txt / sitemap.xml ---------------------------------------
urlpatterns += [
    path("robots.txt", robots_txt, name="robots-txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap-xml"),
]

# --- Arayüz (SPA) --------------------------------------------------------
# Yukarıdaki hiçbir desenle eşleşmeyen (api/, admin/, static/, media/ ile
# başlamayan) her GET isteği, istemci tarafı yönlendiricinin (frontend/static/js)
# yönetebilmesi için tek sayfa uygulamasının index.html'ine düşer. `spa_view`
# rota bazlı SEO meta verisi (title/description/robots) enjekte eder (bkz.
# apps.core.seo). Bu satır EN SONDA olmalı, aksi halde diğer tüm route'ları
# gölgeler.
urlpatterns += [
    re_path(r"^(?!api/|admin/|static/|media/).*$", spa_view, name="spa"),
]
