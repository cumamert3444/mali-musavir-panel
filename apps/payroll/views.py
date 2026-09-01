from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import NotFound

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
