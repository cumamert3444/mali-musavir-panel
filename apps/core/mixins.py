"""
Cok kiracili (multi-tenant) veri izolasyonunu saglayan ortak yapi taslari.

Tasarim: "shared database, shared schema" yaklasimi -- her tenant-scoped
model bir `office` (Office/tenant) alanina sahiptir ve varsayilan manager bu
alana gore filtrelenir. Boylece bir ofisin verisi, kod hatasi olmadikca,
baska bir ofisin sorgusuna asla karismaz.

Super admin (is_superuser) gibi tum ofisleri gormesi gereken durumlar icin
`all_objects` manager'i acikca kullanilmalidir -- sessiz bir "hepsini goster"
modu yoktur, bilinçli bir tercih gerekir.
"""
from django.db import models


class TenantScopedQuerySet(models.QuerySet):
    def for_office(self, office):
        return self.filter(office=office)


class TenantScopedManager(models.Manager.from_queryset(TenantScopedQuerySet)):
    """Varsayilan manager: `Model.objects` -- hicbir filtre uygulamaz, sorumluluk
    view/servis katmanindadir (bkz. apps.core.permissions ve viewset'lerdeki
    get_queryset override'lari). Bu manager sadece `for_office()` kisayolunu
    tum tenant-scoped modellerde tutarli hale getirir."""


class TenantScopedModel(models.Model):
    """Tenant-scoped modeller icin soyut taban sinif.

    `office` alani zorunludur; ilgili tabloya erisen her queryset, view
    katmaninda `TenantScopedViewSetMixin` araciligiyla otomatik olarak
    `request.office` ile filtrelenir (bkz. apps.core.views).
    """

    office = models.ForeignKey(
        "tenants.Office",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
    )

    objects = TenantScopedManager()

    class Meta:
        abstract = True
