import datetime as dt

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.legal_notices.models import LegalNotification
from apps.legal_notices.serializers import LegalNotificationSerializer


class LegalNotificationViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """e-Tebligat / resmi bildirim takibi."""

    queryset = LegalNotification.objects.select_related("client", "assigned_to", "document")
    serializer_class = LegalNotificationSerializer
    filterset_fields = ["status", "source", "client"]
    search_fields = ["title", "notification_number", "client__title"]
    ordering_fields = ["received_at", "response_due_date"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office)
        log_action(self.request, action="create", model_name="LegalNotification", object_id=instance.id)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request, action="update", model_name="LegalNotification", object_id=instance.id)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        """`GET .../legal-notifications/upcoming/?days=7` -- yanit suresi
        yaklasan/gecmis tebligatlar."""
        try:
            days = int(request.query_params.get("days", 7))
        except ValueError:
            days = 7
        horizon = timezone.localdate() + dt.timedelta(days=days)
        queryset = (
            self.get_queryset()
            .filter(response_due_date__isnull=False, response_due_date__lte=horizon)
            .exclude(status__in=[LegalNotification.Status.RESPONDED, LegalNotification.Status.NOT_APPLICABLE])
            .order_by("response_due_date")
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)
