"""Beyanname donem/vade hesaplama ve DeclarationInstance uretim mantigi.

Bu modul saf fonksiyonlar + iki orkestrasyon fonksiyonundan olusur, boylece
hem yonetim komutundan (`generate_declaration_instances`) hem Celery
gorevinden hem de API'den (ornek: yeni musteri beyanname turune abone
oldugunda ilk instance'lari uretmek icin) cagrilabilir.
"""
from __future__ import annotations

import calendar
import datetime as dt

from apps.clients.models import Client
from apps.declarations.models import ClientDeclarationSubscription, DeclarationInstance, DeclarationType


def add_months(source: dt.date, months: int) -> dt.date:
    month_index = source.month - 1 + months
    year = source.year + month_index // 12
    month = month_index % 12 + 1
    day = min(source.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)


def compute_due_date(declaration_type: DeclarationType, period_end: dt.date) -> dt.date:
    """`period_end`e gore vade tarihini hesaplar (bkz. DeclarationType
    doc-string'i: due_month_offset + due_day kurali)."""
    target_month_date = add_months(period_end, declaration_type.due_month_offset)
    last_day_of_month = calendar.monthrange(target_month_date.year, target_month_date.month)[1]
    day = last_day_of_month if declaration_type.due_day in (0, None) else min(declaration_type.due_day, last_day_of_month)
    return dt.date(target_month_date.year, target_month_date.month, day)


def first_period_for(declaration_type: DeclarationType, on_or_after: dt.date) -> tuple[dt.date, dt.date, str]:
    """`on_or_after` tarihini iceren (veya ondan sonraki ilk) donemi
    (period_start, period_end, period_label) olarak dondurur."""
    if declaration_type.period == DeclarationType.Period.MONTHLY:
        start = on_or_after.replace(day=1)
        end = dt.date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
        label = start.strftime("%Y-%m")
        return start, end, label

    if declaration_type.period == DeclarationType.Period.QUARTERLY:
        quarter_index = (on_or_after.month - 1) // 3  # 0..3
        start_month = quarter_index * 3 + 1
        start = dt.date(on_or_after.year, start_month, 1)
        end_month = start_month + 2
        end = dt.date(start.year, end_month, calendar.monthrange(start.year, end_month)[1])
        label = f"{start.year}-Q{quarter_index + 1}"
        return start, end, label

    # YEARLY
    start = dt.date(on_or_after.year, 1, 1)
    end = dt.date(on_or_after.year, 12, 31)
    label = str(start.year)
    return start, end, label


def next_period(declaration_type: DeclarationType, previous_period_end: dt.date) -> tuple[dt.date, dt.date, str]:
    """Bir onceki donemin bitisinden sonraki donemi dondurur."""
    return first_period_for(declaration_type, previous_period_end + dt.timedelta(days=1))


def ensure_instance(
    client: Client, declaration_type: DeclarationType, period_start: dt.date, period_end: dt.date, period_label: str
) -> DeclarationInstance:
    due_date = compute_due_date(declaration_type, period_end)
    instance, _created = DeclarationInstance.objects.get_or_create(
        client=client,
        declaration_type=declaration_type,
        period_start=period_start,
        defaults={
            "office": client.office,
            "period_end": period_end,
            "period_label": period_label,
            "due_date": due_date,
        },
    )
    return instance


def generate_instances_for_subscription(
    subscription: ClientDeclarationSubscription, *, horizon_end: dt.date
) -> list[DeclarationInstance]:
    """Bir musteri-beyanname abonelik cifti icin, en son uretilmis donemden
    (veya abonelik baslangicindan) `horizon_end`e kadar eksik olan tum
    DeclarationInstance kayitlarini olusturur (idempotent)."""
    if not subscription.is_active or not subscription.declaration_type.is_active:
        return []

    declaration_type = subscription.declaration_type
    client = subscription.client

    last_instance = (
        DeclarationInstance.objects.filter(client=client, declaration_type=declaration_type)
        .order_by("-period_end")
        .first()
    )

    if last_instance:
        period_start, period_end, period_label = next_period(declaration_type, last_instance.period_end)
    else:
        start_from = subscription.starts_on or client.start_date or dt.date.today().replace(month=1, day=1)
        period_start, period_end, period_label = first_period_for(declaration_type, start_from)

    created = []
    guard = 0
    while period_start <= horizon_end and guard < 240:  # guvenlik siniri: sonsuz donguyu engeller
        guard += 1
        created.append(ensure_instance(client, declaration_type, period_start, period_end, period_label))
        period_start, period_end, period_label = next_period(declaration_type, period_end)

    return created


def generate_upcoming_declaration_instances(*, months_ahead: int = 2) -> int:
    """Tum aktif musteri-beyanname aboneliklari icin, bugunden itibaren
    `months_ahead` ay sonrasina kadar eksik DeclarationInstance kayitlarini
    uretir. Celery gorevi ve yonetim komutu tarafindan cagrilir."""
    horizon_end = add_months(dt.date.today(), months_ahead)
    total = 0
    subscriptions = ClientDeclarationSubscription.objects.filter(
        is_active=True, declaration_type__is_active=True, client__status="active"
    ).select_related("client", "declaration_type")
    for subscription in subscriptions:
        total += len(generate_instances_for_subscription(subscription, horizon_end=horizon_end))
    return total
