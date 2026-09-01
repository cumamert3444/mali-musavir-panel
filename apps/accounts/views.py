from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Membership
from apps.accounts.serializers import (
    InviteMemberSerializer,
    MembershipSerializer,
    MeSerializer,
    RegisterOfficeSerializer,
)
from apps.core.audit import log_action
from apps.core.permissions import HasActiveOffice, HasOfficeRole
from apps.core.views import TenantScopedViewSetMixin


class RegisterOfficeView(APIView):
    """`POST /api/v1/accounts/register-office/`

    Yeni bir ofis (tenant) ve ilk kullanici (owner) olusturur. Herkese acik --
    yeni bir mali musavirlik ofisinin sisteme kaydolma yolu budur."""

    permission_classes = [AllowAny]
    serializer_class = RegisterOfficeSerializer

    def post(self, request, *args, **kwargs):
        serializer = RegisterOfficeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        log_action(
            action="create",
            office=result["office"],
            actor=result["owner"],
            model_name="Office",
            object_id=result["office"].id,
            metadata={"event": "office_registered"},
        )
        return Response(
            {
                "office_id": result["office"].id,
                "office_name": result["office"].name,
                "owner_email": result["owner"].email,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(RetrieveUpdateAPIView):
    """`GET/PATCH /api/v1/accounts/me/` -- oturum acmis kullanicinin profili
    ve uye oldugu tum ofis/rol bilgileri."""

    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class MembershipViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Aktif ofisin ekip uyeleri: listeleme, davet etme (create), rol
    guncelleme, pasife alma. Yazma islemleri sadece OWNER rolune acik."""

    queryset = Membership.objects.select_related("user", "office").all()
    serializer_class = MembershipSerializer
    permission_classes = [HasActiveOffice, HasOfficeRole]
    filterset_fields = ["role", "is_active"]
    search_fields = ["user__email", "user__first_name", "user__last_name"]

    @property
    def required_roles(self):
        if self.action in {"list", "retrieve"}:
            return None
        return [Membership.Role.OWNER]

    def create(self, request, *args, **kwargs):
        serializer = InviteMemberSerializer(data=request.data, context={"office": request.office})
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        log_action(request, action="create", model_name="Membership", object_id=membership.id)
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        membership = self.get_object()
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        log_action(request, action="update", model_name="Membership", object_id=membership.id,
                   metadata={"event": "deactivated"})
        return Response(MembershipSerializer(membership).data)
