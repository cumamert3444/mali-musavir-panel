"""SPA'yı servis eden view için rota bazlı SEO meta verisi.

Panel istemci tarafında (vanilla JS) render edilen bir SPA olduğundan,
gerçek anlamda "her sayfa için ayrı sunucu render'ı" yoktur -- ama Django
zaten HER isteği bu şablonu döndürdüğü için, `request.path`'e bakarak
BİLİNEN herkese açık pazarlama rotaları (/, /login, /register, /gizlilik-
politikasi, ...) için gerçek/anlamlı `<title>`, meta açıklama ve
`index,follow` robots direktifi; girişli uygulama ekranları (dashboard,
müşteriler, faturalar vb.) için ise `noindex,nofollow` (bu ekranlar zaten
kimlik doğrulama gerektirir, aranabilir olmaları anlamsız/istenmeyen) veren
BASİT ama gerçek bir sunucu taraflı SEO katmanı kurulmuş olur.
"""
from __future__ import annotations

SITE_NAME = "Müşavir Asistanı"

DEFAULT_DESCRIPTION = (
    "Müşavir Asistanı; mali müşavirlik ofisleri için müşteri takibi, beyanname takvimi, "
    "e-Tebligat izleme, vergi/SGK borç matrisi, faturalama ve öğrenen hesap kodu önerisi "
    "sunan tek panelli SaaS'tır."
)

# path -> {title, description, robots (opsiyonel, varsayilan "index, follow")}
PUBLIC_ROUTES: dict[str, dict] = {
    "/": {
        "title": f"{SITE_NAME} — Mali Müşavirlik Ofis Paneli",
        "description": DEFAULT_DESCRIPTION,
    },
    "/login": {
        "title": f"Giriş Yap — {SITE_NAME}",
        "description": "Ofis hesabınızla Müşavir Asistanı paneline giriş yapın.",
    },
    "/register": {
        "title": f"Ücretsiz Deneyin — {SITE_NAME}",
        "description": "Ofisiniz için ücretsiz Müşavir Asistanı hesabı oluşturun, kurulum gerektirmez.",
    },
    "/gizlilik-politikasi": {
        "title": f"Gizlilik Politikası — {SITE_NAME}",
        "description": "Müşavir Asistanı gizlilik politikası ve kişisel verilerin korunmasına ilişkin bilgilendirme.",
    },
    "/kvkk": {
        "title": f"KVKK Aydınlatma Metni — {SITE_NAME}",
        "description": "6698 sayılı KVKK kapsamında Müşavir Asistanı aydınlatma metni.",
    },
    "/durum": {
        "title": f"Sistem Durumu — {SITE_NAME}",
        "description": "Müşavir Asistanı API ve veritabanı servislerinin canlı durumu.",
    },
    "/tesekkurler": {
        "title": f"Teşekkürler — {SITE_NAME}",
        "robots": "noindex, nofollow",
        "description": "Talebiniz alındı.",
    },
}

APP_DEFAULT = {
    "title": f"Panel — {SITE_NAME}",
    "description": DEFAULT_DESCRIPTION,
    "robots": "noindex, nofollow",
}


def resolve_seo_context(path: str) -> dict:
    entry = PUBLIC_ROUTES.get(path.rstrip("/") or "/")
    if entry is None:
        entry = APP_DEFAULT
    return {
        "seo_title": entry.get("title", APP_DEFAULT["title"]),
        "seo_description": entry.get("description", DEFAULT_DESCRIPTION),
        "seo_robots": entry.get("robots", "index, follow"),
        "seo_is_home": path.rstrip("/") in ("", "/") or path == "/",
    }
