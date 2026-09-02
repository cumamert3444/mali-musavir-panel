from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership, User
from apps.core.audit import log_action
from apps.core.tenant import office_access_allowed, resolve_office
from apps.tenants.models import Office, Subscription, SubscriptionPlan
from apps.tenants.serializers import OfficeAdminSerializer, OfficeSerializer, SubscriptionPlanAdminSerializer


class MyOfficeView(APIView):
    """`GET /api/v1/tenants/my-office/` -- aktif ofis bilgisi.

    `PATCH /api/v1/tenants/my-office/` -- ofis sahibinin (OWNER) kendi
    ofisinin temel bilgilerini ve **API modunu** (`api_enabled`)
    acip/kapatabilecegi uc nokta. API modunu aktiflestirmenin normal yolu
    budur: `PATCH {"api_enabled": true}` sonrasinda `/api/v1/apikeys/keys/`
    ile bir anahtar olusturulur.
    """

    permission_classes = [IsAuthenticated]

    def _get_office(self, request):
        office = getattr(request, "office", None) or resolve_office(request)
        return office

    def get(self, request):
        office = self._get_office(request)
        if office is None:
            return Response({"detail": "Aktif ofis bulunamadi."}, status=status.HTTP_404_NOT_FOUND)
        return Response(OfficeSerializer(office).data)

    def patch(self, request):
        office = self._get_office(request)
        if office is None:
            return Response({"detail": "Aktif ofis bulunamadi."}, status=status.HTTP_404_NOT_FOUND)
        if not office_access_allowed(request, office):
            return Response({"detail": "Bu ofise erisim yetkiniz yok."}, status=status.HTTP_403_FORBIDDEN)

        is_owner = request.user.is_superuser or Membership.objects.filter(
            user=request.user, office=office, role=Membership.Role.OWNER, is_active=True
        ).exists()
        if not is_owner:
            return Response(
                {"detail": "Ofis ayarlarini yalnizca ofis sahibi (owner) degistirebilir."},
                status=status.HTTP_403_FORBIDDEN,
            )

        allowed_fields = {"name", "legal_name", "tax_number", "tax_office", "address", "phone", "email",
                           "api_enabled"}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        serializer = OfficeSerializer(office, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        log_action(request, action="update", model_name="Office", object_id=office.id,
                   metadata={"changed_fields": list(data.keys())})
        return Response(OfficeSerializer(office).data)


class OfficeAdminViewSet(viewsets.ModelViewSet):
    """Sadece super admin (SaaS sahibi) icin: tum ofislerin listesi/yonetimi."""

    queryset = Office.objects.all().select_related("subscription", "subscription__plan")
    serializer_class = OfficeAdminSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["name", "legal_name", "tax_number"]
    filterset_fields = ["is_active", "api_enabled"]

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        """`POST admin/offices/<id>/toggle_active/` -- ofisi aktif/pasif yapar
        (ör. odeme gecikmis/kotayi asmis bir ofisi gecici olarak durdurmak icin)."""
        office = self.get_object()
        office.is_active = not office.is_active
        office.save(update_fields=["is_active"])
        log_action(request, action="update", model_name="Office", object_id=office.id,
                   metadata={"event": "superadmin_toggle_active", "is_active": office.is_active})
        return Response(OfficeAdminSerializer(office).data)


class PlatformStatsView(APIView):
    """`GET /api/v1/tenants/admin/stats/` -- Süper Admin panosu için platform
    geneli özet sayılar (ofis/kullanıcı/müşteri sayısı, plan dağılımı vb.)."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.clients.models import Client

        total_offices = Office.objects.count()
        active_offices = Office.objects.filter(is_active=True).count()
        total_users = User.objects.count()
        total_clients = Client.objects.count()

        plan_breakdown = list(
            Subscription.objects.values("plan__name", "plan__code")
            .annotate(office_count=Count("id"))
            .order_by("-office_count")
        )
        status_breakdown = list(
            Subscription.objects.values("status").annotate(count=Count("id")).order_by("-count")
        )
        recent_offices = OfficeAdminSerializer(
            Office.objects.select_related("subscription", "subscription__plan").order_by("-created_at")[:8],
            many=True,
        ).data

        return Response({
            "generated_at": timezone.now(),
            "total_offices": total_offices,
            "active_offices": active_offices,
            "inactive_offices": total_offices - active_offices,
            "total_users": total_users,
            "total_clients": total_clients,
            "plan_breakdown": plan_breakdown,
            "status_breakdown": status_breakdown,
            "recent_offices": recent_offices,
        })


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """Sadece super admin icin: platformdaki tüm kullanıcıların ve hangi
    ofis(ler)e üye olduklarının salt-okunur listesi (gözetim/denetim)."""

    queryset = User.objects.all().prefetch_related("memberships__office").order_by("-date_joined")
    permission_classes = [IsAdminUser]
    search_fields = ["email", "first_name", "last_name"]
    filterset_fields = ["is_active", "is_staff"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        data = [self._serialize(u) for u in (page or queryset)]
        return self.get_paginated_response(data) if page is not None else Response(data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self._serialize(self.get_object()))

    @staticmethod
    def _serialize(user):
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined,
            "memberships": [
                {"office": m.office_id, "office_name": m.office.name, "role": m.role, "is_active": m.is_active}
                for m in user.memberships.all()
            ],
        }

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response({"detail": "Kendi hesabınızı buradan pasife alamazsınız."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        log_action(request, action="update", model_name="User", object_id=user.id,
                   metadata={"event": "superadmin_toggle_active", "is_active": user.is_active})
        return Response(self._serialize(user))


class SubscriptionPlanAdminViewSet(viewsets.ModelViewSet):
    """Sadece super admin icin: SaaS paket/fiyatlandırma tanımlarının yönetimi."""

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanAdminSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["name", "code"]
    filterset_fields = ["is_active"]
