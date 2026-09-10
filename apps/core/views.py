from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.core.account_learning import suggest_account_code
from apps.core.models import AccountCodeMemory, AuditLog
from apps.core.permissions import HasActiveOffice
from apps.core.serializers import AccountCodeMemorySerializer, AuditLogSerializer
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


class AccountCodeMemoryViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Ofisin "öğrenilmiş" hesap kodu eşleşmeleri -- bkz.
    apps.core.models.AccountCodeMemory ve apps.core.account_learning
    docstring'leri (dürüst kapsam notu: LLM/dış AI sağlayıcı DEĞİL, basit
    ücretsiz bir kural/frekans motoru).

    Muhasebeci burada yanlış öğrenilmiş bir eşleşmeyi görüp silebilir
    (`DELETE`) -- şeffaflık için salt-okunur değil, tam CRUD."""

    queryset = AccountCodeMemory.objects.all()
    serializer_class = AccountCodeMemorySerializer
    filterset_fields = ["source_app"]
    search_fields = ["match_key", "account_code"]
    ordering_fields = ["hit_count", "last_used_at", "created_at"]

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """`GET .../account-code-memory/suggest/?source_app=einvoice&text=...`
        -- verilen serbest metin için (varsa) öğrenilmiş bir hesap kodu
        önerisi döner. Tam eşleşme bulunamazsa `{"suggestion": null}` döner
        -- bu normal bir durumdur, henüz o desen için hiçbir şey
        öğrenilmemiş demektir."""
        source_app = request.query_params.get("source_app")
        text = request.query_params.get("text", "")
        if source_app not in ("bank_statement", "einvoice"):
            return Response({"detail": "'source_app' 'bank_statement' veya 'einvoice' olmalı."}, status=400)
        suggestion = suggest_account_code(office=request.office, source_app=source_app, raw_text=text)
        return Response({"suggestion": suggestion})
