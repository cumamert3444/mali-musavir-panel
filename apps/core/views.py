from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from apps.core.models import AuditLog
from apps.core.permissions import HasActiveOffice
from apps.core.serializers import AuditLogSerializer
from apps.core.tenant import office_access_allowed, resolve_office


class TenantScopedViewSetMixin:
    """Tum tenant-scoped ModelViewSet'lerin miras alacagi ortak mixin.

    - JWT ile kimligi dogrulanan istekler icin `request.office`'i (henuz
      cozulmemisse) DRF kimlik dogrulamasindan SONRA cozer.
    - Sorgu kumesini otomatik olarak aktif ofisle filtreler.
    - Yeni kayitlarda `office` alanini otomatik doldurur.
    """

    permission_classes = [HasActiveOffice]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if getattr(request, "office", None) is None:
            request.office = resolve_office(request)
        if request.office is not None and not office_access_allowed(request, request.office):
            raise PermissionDenied("Bu ofise erisim yetkiniz yok.")

    def get_queryset(self):
        queryset = super().get_queryset()
        office = getattr(self.request, "office", None)
        if office is None:
            return queryset.none()
        return queryset.filter(office=office)

    def perform_create(self, serializer):
        serializer.save(office=self.request.office)


class AuditLogViewSet(TenantScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """Ofisin kendi aktivite gunlugu -- salt okunur (Hattat Musavir'deki
    'Raporlar -> Islem Raporlari' ekranindan ilhamla, bkz. proje notlari).

    `AuditLog` bir `TenantScopedModel` degil (super admin tum ofisleri
    gorebilmeli) ama `office` alani var; `TenantScopedViewSetMixin.get_queryset`
    yine de dogru sekilde `office=request.office` ile filtreler."""

    queryset = AuditLog.objects.select_related("actor").all()
    serializer_class = AuditLogSerializer
    filterset_fields = ["action", "model_name"]
    search_fields = ["actor_label", "model_name", "object_id", "path"]
    ordering_fields = ["created_at"]
