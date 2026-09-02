from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from apps.clients.models import Client
from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.payroll.models import Employee, PayrollRecord
from apps.payroll.serializers import EmployeeSerializer, PayrollRecordSerializer


class _NestedUnderClientMixin:
    def get_client(self) -> Client:
        office = getattr(self.request, "office", None)
        if office is None:
            raise NotFound("Aktif ofis bulunamadi.")
        return get_object_or_404(Client, pk=self.kwargs["client_pk"], office=office)


class EmployeeViewSet(_NestedUnderClientMixin, TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """`clients/<client_pk>/employees/` -- musterinin personel listesi."""

    serializer_class = EmployeeSerializer
    filterset_fields = ["status", "employment_type"]
    search_fields = ["full_name", "tc_no", "sgk_sicil_no"]

    def get_queryset(self):
        return Employee.objects.select_related("client").prefetch_related("payroll_records").filter(
            client=self.get_client()
        )

    def perform_create(self, serializer):
        instance = serializer.save(client=self.get_client())
        log_action(self.request, action="create", model_name="Employee", object_id=instance.id)

    @action(detail=True, methods=["post"], url_path="mark-sgk-entry-notified")
    def mark_sgk_entry_notified(self, request, client_pk=None, pk=None):
        """SGK işe giriş bildiriminin fiilen yapıldığını (e-Bildirge
        portalından) manuel olarak işaretler -- gerçek bir SGK portal
        entegrasyonu değildir, bir kontrol listesi (checklist) adımıdır."""
        employee = self.get_object()
        employee.sgk_entry_notified = True
        employee.sgk_entry_notified_at = timezone.now()
        employee.save(update_fields=["sgk_entry_notified", "sgk_entry_notified_at"])
        log_action(request, action="update", model_name="Employee", object_id=employee.id,
                   metadata={"event": "sgk_entry_notified"})
        return Response(EmployeeSerializer(employee).data)

    @action(detail=True, methods=["post"], url_path="mark-sgk-exit-notified")
    def mark_sgk_exit_notified(self, request, client_pk=None, pk=None):
        employee = self.get_object()
        employee.sgk_exit_notified = True
        employee.sgk_exit_notified_at = timezone.now()
        employee.save(update_fields=["sgk_exit_notified", "sgk_exit_notified_at"])
        log_action(request, action="update", model_name="Employee", object_id=employee.id,
                   metadata={"event": "sgk_exit_notified"})
        return Response(EmployeeSerializer(employee).data)


class _NestedUnderEmployeeMixin:
    def get_employee(self) -> Employee:
        office = getattr(self.request, "office", None)
        if office is None:
            raise NotFound("Aktif ofis bulunamadi.")
        return get_object_or_404(
            Employee, pk=self.kwargs["employee_pk"], client_id=self.kwargs["client_pk"], client__office=office
        )


class PayrollRecordViewSet(_NestedUnderEmployeeMixin, TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """`clients/<client_pk>/employees/<employee_pk>/payroll-records/`"""

    serializer_class = PayrollRecordSerializer
    filterset_fields = ["status"]

    def get_queryset(self):
        return PayrollRecord.objects.filter(employee=self.get_employee())

    def perform_create(self, serializer):
        instance = serializer.save(employee=self.get_employee())
        log_action(self.request, action="create", model_name="PayrollRecord", object_id=instance.id)
