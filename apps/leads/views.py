from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.leads.models import DemoRequest
from apps.leads.serializers import DemoRequestAdminSerializer, DemoRequestCreateSerializer


class DemoRequestCreateView(APIView):
    """`POST /api/v1/leads/demo-request/` -- herkese açık (AllowAny) demo/
    iletişim talebi formu. Ofis/kimlik doğrulama gerektirmez -- landing
    sayfasındaki 'Demo İsteyin' formunun gittiği yer burasıdır."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DemoRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Talebiniz alındı, en kısa sürede size dönüş yapacağız."}, status=201)


class DemoRequestAdminViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Sadece Süper Admin: gelen demo/iletişim taleplerinin listesi ve
    durum güncellemesi (bkz. apps.tenants -- SuperAdmin paneli deseniyle
    tutarlı)."""

    queryset = DemoRequest.objects.all()
    serializer_class = DemoRequestAdminSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["status"]
    search_fields = ["full_name", "email", "office_name"]
