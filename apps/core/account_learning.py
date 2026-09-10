"""Basit, ücretsiz, ofis-bazlı "öğrenen" hesap kodu öneri motoru.

DÜRÜST KAPSAM NOTU: Bu bir LLM/üretken yapay zeka DEĞİLDİR -- Anthropic,
OpenAI, Groq gibi hiçbir dış sağlayıcıya bağlanmaz, API anahtarı ya da
internet erişimi gerektirmez. Muhasebecinin daha önce onayladığı
"açıklama/karşı taraf -> hesap kodu" eşleşmelerini `AccountCodeMemory`
tablosunda biriktirir (bkz. apps.core.models.AccountCodeMemory docstring'i)
ve yeni bir kayıt geldiğinde aynı deseni arayıp bir ÖNERİ döner. Kasıtlı
olarak basit tutulmuştur (yalnızca tam eşleşme, bulanık/fuzzy eşleşme
YOKTUR) -- yanlış ama "kendinden emin" bir öneri sunmaktansa hiç öneri
sunmamak tercih edilmiştir.
"""
from __future__ import annotations

import re

from django.db.models import F

TR_MAP = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")

_NOISE_WORDS = {
    "REF", "REFNO", "FIS", "FISNO", "DEKONT", "ISLEM", "ISLEMNO", "NO",
    "TARIH", "SAAT", "ISLEMI", "ODEME", "ODEMESI", "TAHSILAT", "TAHSILATI",
    "HAVALE", "EFT", "TRANSFER", "VE",
}


def normalize_match_key(text: str, *, max_tokens: int = 6) -> str:
    """Banka açıklaması / karşı taraf unvanı gibi serbest metni, tarih ve
    referans numarası gibi işlemden işleme değişen kısımları ATARAK, kararlı
    bir "eşleşme anahtarı"na çevirir. Örnek:
    "SGK PRIM ODEMESI 01.09.2026 REF:AB12345" -> "SGK PRIM"
    Bu bir kesinlik garantisi değildir -- en iyi çaba (best-effort) esaslıdır.
    """
    if not text:
        return ""
    upper = text.upper().translate(TR_MAP)
    upper = re.sub(r"\d{1,2}[./]\d{1,2}[./]\d{2,4}", " ", upper)  # tarihler
    upper = re.sub(r"[^A-Z ]", " ", upper)  # rakam/noktalama -> bosluk
    tokens = [t for t in upper.split() if len(t) > 2 and t not in _NOISE_WORDS]
    return " ".join(tokens[:max_tokens]).strip()


def learn_mapping(*, office, source_app: str, raw_text: str, account_code: str) -> None:
    """Muhasebecinin onayladığı/girdiği bir hesap kodu eşleşmesini kaydeder.
    Sadece insan onaylı verilerle çağrılmalıdır -- sistemin kendi önerileri
    tekrar buraya beslenmemelidir (kendi kendini pekiştiren yanlış önerileri
    önlemek için)."""
    if office is None or not account_code:
        return
    key = normalize_match_key(raw_text)
    if not key:
        return
    from apps.core.models import AccountCodeMemory

    obj, created = AccountCodeMemory.objects.get_or_create(
        office=office, source_app=source_app, match_key=key, account_code=account_code,
        defaults={"hit_count": 1},
    )
    if not created:
        AccountCodeMemory.objects.filter(pk=obj.pk).update(hit_count=F("hit_count") + 1)


def suggest_account_code(*, office, source_app: str, raw_text: str) -> dict | None:
    """Verilen açıklama/karşı taraf için en çok kullanılan hesap kodu
    önerisini döner: {"account_code": ..., "match_key": ..., "hit_count": ...}
    ya da hiçbir tam eşleşme yoksa None."""
    if office is None:
        return None
    key = normalize_match_key(raw_text)
    if not key:
        return None
    from apps.core.models import AccountCodeMemory

    best = (
        AccountCodeMemory.objects.filter(office=office, source_app=source_app, match_key=key)
        .order_by("-hit_count", "-last_used_at")
        .first()
    )
    if not best:
        return None
    return {"account_code": best.account_code, "match_key": key, "hit_count": best.hit_count}
