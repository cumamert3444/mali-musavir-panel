"""SPA host şablonu + robots.txt / sitemap.xml için düz Django view'ları
(DRF değil -- bunlar HTML/metin döner, API değildir)."""
from __future__ import annotations

import time

from django.conf import settings
from django.db import connections
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.core.seo import PUBLIC_ROUTES, resolve_seo_context


def spa_view(request, *args, **kwargs):
    """Tüm SPA rotaları için ortak giriş noktası -- bkz. apps.core.seo."""
    context = resolve_seo_context(request.path)
    context["site_url"] = getattr(settings, "SITE_URL", "").rstrip("/")
    context["canonical_url"] = context["site_url"] + request.path
    context["ga4_measurement_id"] = getattr(settings, "GA4_MEASUREMENT_ID", "")
    context["meta_pixel_id"] = getattr(settings, "META_PIXEL_ID", "")
    context["whatsapp_number"] = getattr(settings, "WHATSAPP_CONTACT_NUMBER", "")
    context["office_address"] = getattr(settings, "OFFICE_PUBLIC_ADDRESS", "")
    return render(request, "spa.html", context)


@require_GET
def robots_txt(request):
    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /api/",
        "Disallow: /admin/",
        "Disallow: /dashboard",
        "Disallow: /clients",
        "Disallow: /invoices",
        "Disallow: /tasks",
        "Disallow: /declarations",
        "Disallow: /tax-debts",
        "Disallow: /pos-reports",
        "Disallow: /documents",
        "Disallow: /legal-notices",
        "Disallow: /team",
        "Disallow: /settings",
        "Disallow: /admin-panel",
        "",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@require_GET
def sitemap_xml(request):
    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    urls = []
    for path, entry in PUBLIC_ROUTES.items():
        if entry.get("robots", "index").startswith("noindex"):
            continue
        priority = "1.0" if path == "/" else "0.6"
        urls.append(f"  <url><loc>{site_url}{path}</loc><priority>{priority}</priority></url>")

    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    return HttpResponse(body, content_type="application/xml")


@require_GET
def status_check(request):
    """`GET /api/v1/status/` -- GERÇEK bir canlı durum kontrolü (herkese
    açık, kimlik doğrulama gerektirmez). Uydurma bir 'uptime %99.9' rakamı
    GÖSTERMEZ -- yalnızca şu anda veritabanına gerçekten bağlanılabiliyor
    mu, onu ölçer. `/durum` sayfası (frontend) bu uç noktayı çağırır."""
    checks = {}
    overall_ok = True

    start = time.monotonic()
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 -- durum sayfasi icin genis yakalama kasitli
        checks["database"] = {"status": "error", "detail": str(exc)}
        overall_ok = False
    checks["database"]["response_time_ms"] = round((time.monotonic() - start) * 1000, 1)

    checks["api"] = {"status": "ok"}

    payload = {
        "status": "operational" if overall_ok else "degraded",
        "checked_at": timezone.now().isoformat(),
        "checks": checks,
    }
    return JsonResponse(payload, status=200 if overall_ok else 503)
