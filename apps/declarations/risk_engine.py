"""Beyanname Kontrol & Çapraz Eşleştirme Motoru.

Rakip ürünlerin (özellikle Hattat Müşavir/Hattat Entegre) öne çıkardığı
"KDV matrahı ile ciro/e-fatura toplamını, Muhtasar ile SGK prim
bildirgelerini otomatik karşılaştırıp Riskli Mükellef/Matrah Uyumsuzluğu
uyarısı veren denetim modülü" özelliğinin karşılığı.

ÖNEMLİ - dürüst kapsam sınırı: Bu panelde müşterinin GİB'e bildirdiği gerçek
e-Fatura/e-Arşiv toplamlarını veya SGK'nın onayladığı prim tutarlarını
GERÇEK ZAMANLI çeken bir resmi entegrasyon YOKTUR (bu, GİB/SGK'nın kendi
kurumsal API'lerine erişim ve e-imza gerektirir). Bunun yerine, muhasebeci
beyannameyi onayladığında beyan edilen rakamları
`DeclarationInstance.declared_amount` alanına kendisi girer; bu modül o
GİRİLMİŞ rakamları, panelde zaten tutulan diğer verilerle (bordro/SGK prim
tutarları, önceki dönemler) çapraz karşılaştırarak tutarsızlıkları
otomatik olarak işaretler. Gerçek GİB/SGK API entegrasyonu backlog'dadır.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from django.db.models import Sum

from apps.declarations.models import DeclarationInstance, DeclarationType
from apps.payroll.models import PayrollRecord

# Bu esikler makul varsayilanlardir; ofis ihtiyaclarina gore ileride
# ayarlardan degistirilebilir hale getirilebilir (bkz. backlog).
MUHTASAR_SGK_TOLERANCE = Decimal("0.15")  # %15 uzeri fark -> uyari
MATRAH_VOLATILITY_TOLERANCE = Decimal("0.50")  # onceki donem ortalamasindan %50 sapma -> uyari
LOOKBACK_PERIODS = 3


@dataclass
class RiskFlag:
    client_id: int
    client_title: str
    declaration_instance_id: int
    period_label: str
    risk_type: str
    severity: str  # "high" | "medium"
    message: str
    details: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "client_id": self.client_id,
            "client_title": self.client_title,
            "declaration_instance_id": self.declaration_instance_id,
            "period_label": self.period_label,
            "risk_type": self.risk_type,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


def _pct_diff(a: Decimal, b: Decimal) -> Decimal:
    """`a` ile `b` arasindaki oransal farki (buyuk olana gore) dondurur."""
    base = max(abs(a), abs(b))
    if base == 0:
        return Decimal("0")
    return abs(a - b) / base


def check_muhtasar_vs_sgk(office) -> list[RiskFlag]:
    """Muhtasar beyannamesinde bildirilen ucret matrahi (declared_amount) ile
    ayni musteri/donem icin bordro kayitlarindaki brut ucret toplamini
    karsilastirir. Ikisi de girilmisse ve fark toleransi asiyorsa uyari
    uretir -- Hattat'in 'Muhtasar-SGK karsilastirma' ozelliginin karsiligi."""
    flags: list[RiskFlag] = []

    muhtasar_instances = (
        DeclarationInstance.objects.filter(
            office=office, declaration_type__code="muhtasar", declared_amount__isnull=False
        )
        .select_related("client", "declaration_type")
    )

    for instance in muhtasar_instances:
        gross_total = (
            PayrollRecord.objects.filter(
                employee__client=instance.client, period_label=instance.period_label
            ).aggregate(total=Sum("gross_salary"))["total"]
        )
        if gross_total is None:
            continue  # bu donem icin bordro girilmemis -- karsilastirma yapilamaz
        declared = instance.declared_amount
        diff = _pct_diff(declared, Decimal(gross_total))
        if diff > MUHTASAR_SGK_TOLERANCE:
            flags.append(
                RiskFlag(
                    client_id=instance.client_id,
                    client_title=instance.client.title,
                    declaration_instance_id=instance.id,
                    period_label=instance.period_label,
                    risk_type="muhtasar_sgk_mismatch",
                    severity="high" if diff > Decimal("0.30") else "medium",
                    message=(
                        f"Muhtasar'da bildirilen ücret matrahı ({declared:.2f} ₺) ile bordro kayıtlarındaki "
                        f"brüt ücret toplamı ({gross_total:.2f} ₺) arasında %{diff * 100:.0f} fark var."
                    ),
                    details={
                        "declared_amount": str(declared),
                        "payroll_gross_total": str(gross_total),
                        "diff_pct": str((diff * 100).quantize(Decimal("0.1"))),
                    },
                )
            )
    return flags


def check_matrah_volatility(office) -> list[RiskFlag]:
    """Bir mukellefin ayni beyanname turundeki matrahi, kendi son
    donemlerinin ortalamasindan asiri sapiyorsa ('matrah dalgalanmasi')
    isaretler -- e-fatura entegrasyonu olmadan da uygulanabilecek basit
    ama gercek bir anomali kontrolu."""
    flags: list[RiskFlag] = []

    instances = (
        DeclarationInstance.objects.filter(office=office, declared_amount__isnull=False)
        .select_related("client", "declaration_type")
        .order_by("client_id", "declaration_type_id", "period_start")
    )

    grouped: dict[tuple[int, int], list[DeclarationInstance]] = defaultdict(list)
    for instance in instances:
        grouped[(instance.client_id, instance.declaration_type_id)].append(instance)

    for (_client_id, _decl_type_id), items in grouped.items():
        for idx, instance in enumerate(items):
            history = items[max(0, idx - LOOKBACK_PERIODS):idx]
            if len(history) < 2:
                continue  # anlamli bir ortalama icin en az 2 onceki donem gerekli
            avg = sum((h.declared_amount for h in history), Decimal("0")) / len(history)
            if avg == 0:
                continue
            diff = _pct_diff(instance.declared_amount, avg)
            if diff > MATRAH_VOLATILITY_TOLERANCE:
                flags.append(
                    RiskFlag(
                        client_id=instance.client_id,
                        client_title=instance.client.title,
                        declaration_instance_id=instance.id,
                        period_label=instance.period_label,
                        risk_type="matrah_volatility",
                        severity="medium",
                        message=(
                            f"{instance.declaration_type.name} matrahı ({instance.declared_amount:.2f} ₺), "
                            f"son {len(history)} dönem ortalamasından (%{avg:.2f} ₺) %{diff * 100:.0f} sapıyor."
                        ),
                        details={
                            "declared_amount": str(instance.declared_amount),
                            "period_average": str(avg.quantize(Decimal("0.01"))),
                            "diff_pct": str((diff * 100).quantize(Decimal("0.1"))),
                            "declaration_type": instance.declaration_type.name,
                        },
                    )
                )
    return flags


def check_overdue_without_declared_amount(office, *, as_of: dt.date | None = None) -> list[RiskFlag]:
    """Vadesi gecmis ama hala 'beyan edilen tutar' girilmemis kayitlar --
    olasi unutulmus/eksik islenmis beyannameleri yakalar."""
    as_of = as_of or dt.date.today()
    flags: list[RiskFlag] = []
    qs = (
        DeclarationInstance.objects.filter(
            office=office,
            due_date__lt=as_of,
            declared_amount__isnull=True,
        )
        .exclude(status__in=[DeclarationInstance.Status.NOT_APPLICABLE])
        .select_related("client", "declaration_type")
    )
    for instance in qs:
        flags.append(
            RiskFlag(
                client_id=instance.client_id,
                client_title=instance.client.title,
                declaration_instance_id=instance.id,
                period_label=instance.period_label,
                risk_type="missing_declared_amount",
                severity="medium",
                message=(
                    f"{instance.declaration_type.name} ({instance.period_label}) vadesi geçti "
                    f"({instance.due_date:%d.%m.%Y}) ama beyan edilen tutar hâlâ girilmemiş."
                ),
                details={"due_date": instance.due_date.isoformat(), "status": instance.status},
            )
        )
    return flags


def run_all_checks(office) -> dict:
    """Ofis icin tum risk kontrollerini calistirir ve mukellef bazinda
    ozetlenmis sonucu dondurur."""
    all_flags = (
        check_muhtasar_vs_sgk(office)
        + check_matrah_volatility(office)
        + check_overdue_without_declared_amount(office)
    )

    by_client: dict[int, dict] = {}
    for flag in all_flags:
        bucket = by_client.setdefault(
            flag.client_id, {"client_id": flag.client_id, "client_title": flag.client_title, "flags": []}
        )
        bucket["flags"].append(flag.as_dict())

    risky_clients = sorted(by_client.values(), key=lambda b: -len(b["flags"]))

    return {
        "total_flags": len(all_flags),
        "risky_client_count": len(risky_clients),
        "risky_clients": risky_clients,
        "flags": [f.as_dict() for f in all_flags],
    }
