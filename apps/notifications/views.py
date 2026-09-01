from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.views import TenantScopedViewSetMixin
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
