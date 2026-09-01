from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Membership
from apps.apikeys.models import ApiKey
from apps.apikeys.serializers import ApiKeyCreatedResponseSerializer, ApiKeyCreateSerializer, ApiKeySerializer
from apps.core.audit import log_action
from apps.core.permissions import HasActiveOffice, HasOfficeRole
from apps.core.views import TenantScopedViewSetMixin


class ApiKeyViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """Aktif ofisin API anahtarlarini yonetir.

    `POST` ile yeni anahtar olusturmak, "API modunu aktiflestirme" akisinin
    kod tarafidir: Office.api_enabled=True olduktan sonra buradan alinan
    anahtar `X-API-Key` header'i ile dis sistemlerden kullanilabilir.
    """

    queryset = ApiKey.objects.select_related("office", "created_by").all()
    serializer_class = ApiKeySerializer
    permission_classes = [HasActiveOffice, HasOfficeRole]
    http_method_names = ["get", "post", "delete", "head", "options"]

    @property
    def required_roles(self):
        if self.action in {"list", "retrieve"}:
            return None
        return [Membership.Role.OWNER]

    def create(self, request, *args, **kwargs):
        input_serializer = ApiKeyCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        if not request.office.api_enabled:
            return Response(
                {
                    "detail": (
                        "Bu ofis icin API modu kapali. Once ofis ayarlarindan "
                        "(Office.api_enabled) API modunu acin, ardindan anahtar olusturun."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key, raw_key = ApiKey.generate(
            office=request.office,
            name=input_serializer.validated_data["name"],
            created_by=request.user,
        )
        if input_serializer.validated_data.get("expires_at"):
            api_key.expires_at = input_serializer.validated_data["expires_at"]
            api_key.save(update_fields=["expires_at"])

        log_action(request, action="create", model_name="ApiKey", object_id=api_key.id)

        response = ApiKeyCreatedResponseSerializer(api_key, context={"key": raw_key}).data
        response["key"] = raw_key
        return Response(response, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        api_key = self.get_object()
        api_key.is_active = False
        api_key.save(update_fields=["is_active"])
        log_action(request, action="update", model_name="ApiKey", object_id=api_key.id,
                   metadata={"event": "revoked"})
        return Response(ApiKeySerializer(api_key).data)
