from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership
from apps.core.audit import log_action
from apps.core.tenant import office_access_allowed, resolve_office
from apps.tenants.models import Office
from apps.tenants.serializers import OfficeAdminSerializer, OfficeSerializer


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
