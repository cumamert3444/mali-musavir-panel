from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from apps.clients.models import Client, ClientAssignment, ClientContact, ClientGroup, Contract, ServicePackage
from apps.clients.serializers import (
    ClientAssignmentSerializer,
    ClientContactSerializer,
    ClientDetailSerializer,
    ClientGroupSerializer,
    ClientListSerializer,
    ContractSerializer,
    ServicePackageSerializer,
)
from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin


class ServicePackageViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = ServicePackage.objects.all()
    serializer_class = ServicePackageSerializer
    filterset_fields = ["is_active"]
    search_fields = ["name"]


class ClientGroupViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Mukellef gruplama etiketleri (ornek: 'KDV Mukellefi', 'Buyuk Musteri')."""

    queryset = ClientGroup.objects.all()
    serializer_class = ClientGroupSerializer
    search_fields = ["name"]


class ClientViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Client.objects.select_related("package").prefetch_related(
        "contacts", "assignments__user", "contracts", "groups"
    )
    filterset_fields = ["status", "legal_type", "e_invoice_enabled", "e_ledger_enabled", "package", "groups"]
    search_fields = ["title", "tax_number", "city"]
    ordering_fields = ["title", "created_at", "monthly_fee"]

    def get_serializer_class(self):
        if self.action == "list":
            return ClientListSerializer
        return ClientDetailSerializer

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office)
        log_action(self.request, action="create", model_name="Client", object_id=instance.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request, action="update", model_name="Client", object_id=instance.id)

    def perform_destroy(self, instance):
        log_action(self.request, action="delete", model_name="Client", object_id=instance.id)
        instance.delete()


class _NestedUnderClientMixin:
    """`clients/<client_pk>/...` altindaki alt-kaynaklar (iletisim kisisi,
    atama) icin ortak yardimci: musteriyi aktif ofis kapsaminda bulur."""

    def get_client(self):
        office = getattr(self.request, "office", None)
        if office is None:
            raise NotFound("Aktif ofis bulunamadi.")
        return get_object_or_404(Client, pk=self.kwargs["client_pk"], office=office)


class ClientContactViewSet(_NestedUnderClientMixin, TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """`office` alani olmadigi icin TenantScopedViewSetMixin'in get_queryset/
    perform_create'i asagida tamamen ezilir; mixin sadece `initial()` (JWT
    icin ofis cozumleme) ve `HasActiveOffice` izni icin kullanilir."""

    serializer_class = ClientContactSerializer

    def get_queryset(self):
        return ClientContact.objects.filter(client=self.get_client())

    def perform_create(self, serializer):
        serializer.save(client=self.get_client())


class ClientAssignmentViewSet(_NestedUnderClientMixin, TenantScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ClientAssignmentSerializer

    def get_queryset(self):
        return ClientAssignment.objects.select_related("user").filter(client=self.get_client())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["office"] = getattr(self.request, "office", None)
        return context

    def perform_create(self, serializer):
        serializer.save(client=self.get_client())


class ContractViewSet(_NestedUnderClientMixin, TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """`clients/<client_pk>/contracts/` -- musteriyle yapilan hizmet
    sozlesmeleri (rakip urunlerdeki sozlesme-mukellef otomasyonu)."""

    serializer_class = ContractSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Contract.objects.filter(client=self.get_client())

    def perform_create(self, serializer):
        instance = serializer.save(client=self.get_client())
        log_action(self.request, action="create", model_name="Contract", object_id=instance.id)
