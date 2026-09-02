import datetime as dt

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from apps.clients.models import Client
from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.declarations.models import ClientDeclarationSubscription, DeclarationInstance, DeclarationType
from apps.declarations.serializers import (
    ClientDeclarationSubscriptionSerializer,
    DeclarationInstanceSerializer,
    DeclarationTypeSerializer,
)
from apps.declarations.risk_engine import run_all_checks
from apps.declarations.services import add_months, generate_instances_for_subscription


class DeclarationTypeViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = DeclarationType.objects.all()
    serializer_class = DeclarationTypeSerializer
    filterset_fields = ["period", "is_active"]
    search_fields = ["name", "code"]


class DeclarationInstanceViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Beyanname takvimi. `PATCH` genelde sadece `status`/`notes` guncellemek
    icin kullanilir (donem/vade alanlari sistem tarafindan uretilir)."""

    queryset = DeclarationInstance.objects.select_related("client", "declaration_type", "completed_by")
    serializer_class = DeclarationInstanceSerializer
    filterset_fields = ["status", "client", "declaration_type"]
    search_fields = ["client__title", "period_label"]
    ordering_fields = ["due_date", "created_at"]
    # Kayitlar sadece apps.declarations.services (abonelik + celery/komut) ile
    # uretilir; API'den dogrudan POST ile olusturma kapali (period/due_date
    # alanlari read-only ve varsayilan degeri yok).
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        instance = serializer.save()
        if instance.status == DeclarationInstance.Status.SUBMITTED and previous_status != instance.status:
            instance.submitted_at = timezone.now()
            instance.completed_by = self.request.user
            instance.save(update_fields=["submitted_at", "completed_by"])
        log_action(self.request, action="update", model_name="DeclarationInstance", object_id=instance.id)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """`GET .../instances/upcoming/?days=14` -- yaklasan (ve gecikmis)
        beyannameler; ofis genel bakis panosu icin."""
        try:
            days = int(request.query_params.get("days", 14))
        except ValueError:
            days = 14
        horizon = timezone.localdate() + dt.timedelta(days=days)
        queryset = (
            self.get_queryset()
            .filter(due_date__lte=horizon)
            .exclude(status__in=[DeclarationInstance.Status.SUBMITTED, DeclarationInstance.Status.PAID,
                                  DeclarationInstance.Status.NOT_APPLICABLE])
            .order_by("due_date")
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="risk-report")
    def risk_report(self, request):
        """`GET .../declaration-instances/risk-report/` -- Beyanname Kontrol
        & Çapraz Eşleştirme Motoru: Muhtasar/SGK uyumsuzluğu, matrah
        dalgalanması ve beyan edilmemiş vadesi geçmiş kayıtlar için ofis
        genelinde risk özetini döner (bkz. apps.declarations.risk_engine)."""
        if request.office is None:
            return Response({"detail": "Aktif ofis bulunamadi."}, status=404)
        report = run_all_checks(request.office)
        return Response(report)


class ClientDeclarationSubscriptionViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """`clients/<client_pk>/declaration-subscriptions/` -- musterinin
    tabi oldugu beyanname turleri. Yeni bir abonelik olusturulunca ilk
    donem(ler) hemen uretilir."""

    serializer_class = ClientDeclarationSubscriptionSerializer

    def get_client(self) -> Client:
        office = getattr(self.request, "office", None)
        if office is None:
            raise NotFound("Aktif ofis bulunamadi.")
        return get_object_or_404(Client, pk=self.kwargs["client_pk"], office=office)

    def get_queryset(self):
        return ClientDeclarationSubscription.objects.select_related("declaration_type").filter(
            client=self.get_client()
        )

    def perform_create(self, serializer):
        subscription = serializer.save(client=self.get_client())
        horizon_start = timezone.localdate().replace(day=1)
        generate_instances_for_subscription(subscription, horizon_end=add_months(horizon_start, 2))
        log_action(self.request, action="create", model_name="ClientDeclarationSubscription",
                   object_id=subscription.id)
