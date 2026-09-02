from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clients.models import Client
from apps.core.tenant import office_access_allowed, resolve_office
from apps.core.views import TenantScopedViewSetMixin
from apps.notifications.dispatch import DispatchError, dispatch_client_statement
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


class NotificationViewSet(
    TenantScopedViewSetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Sadece istegi yapan kullanicinin KENDI bildirimleri -- ofis
    filtresinin ustune ayrica `recipient=request.user` filtresi eklenir."""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filterset_fields = ["is_read", "category", "channel"]

    def get_queryset(self):
        queryset = super().get_queryset()  # office filtresi burada uygulanir
        return queryset.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"updated": updated})


class DispatchStatementView(APIView):
    """`POST /api/v1/notifications/dispatch-statement/`

    body: `{"client": <id>, "channel": "email"|"whatsapp", "note": "..."}`

    Müşterinin cari hesap ekstresini PDF olarak üretir ve seçilen kanaldan
    gönderir (bkz. apps.notifications.dispatch). WhatsApp sağlayıcısı
    yapılandırılmamışsa net bir hata döner -- asla sahte bir başarı
    yanıtı üretmez."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        office = getattr(request, "office", None) or resolve_office(request)
        if office is None:
            return Response({"detail": "Aktif ofis bulunamadi."}, status=status.HTTP_404_NOT_FOUND)
        if not office_access_allowed(request, office):
            return Response({"detail": "Bu ofise erisim yetkiniz yok."}, status=status.HTTP_403_FORBIDDEN)
        request.office = office

        client_id = request.data.get("client")
        channel = request.data.get("channel", Notification.Channel.EMAIL)
        note = request.data.get("note", "")
        if not client_id:
            return Response({"detail": "'client' alanı zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

        client = get_object_or_404(Client, pk=client_id, office=office)

        try:
            notification = dispatch_client_statement(request=request, client=client, channel=channel, note=note)
        except DispatchError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)
