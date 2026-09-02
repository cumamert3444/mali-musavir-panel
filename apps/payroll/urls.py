from django.urls import path

from apps.payroll.views import EmployeeViewSet, PayrollRecordViewSet

app_name = "payroll"

employee_list = EmployeeViewSet.as_view({"get": "list", "post": "create"})
employee_detail = EmployeeViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
employee_mark_sgk_entry = EmployeeViewSet.as_view({"post": "mark_sgk_entry_notified"})
employee_mark_sgk_exit = EmployeeViewSet.as_view({"post": "mark_sgk_exit_notified"})
payroll_list = PayrollRecordViewSet.as_view({"get": "list", "post": "create"})
payroll_detail = PayrollRecordViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("clients/<int:client_pk>/employees/", employee_list, name="client-employee-list"),
    path("clients/<int:client_pk>/employees/<int:pk>/", employee_detail, name="client-employee-detail"),
    path(
        "clients/<int:client_pk>/employees/<int:pk>/mark-sgk-entry-notified/",
        employee_mark_sgk_entry,
        name="client-employee-mark-sgk-entry",
    ),
    path(
        "clients/<int:client_pk>/employees/<int:pk>/mark-sgk-exit-notified/",
        employee_mark_sgk_exit,
        name="client-employee-mark-sgk-exit",
    ),
    path(
        "clients/<int:client_pk>/employees/<int:employee_pk>/payroll-records/",
        payroll_list,
        name="employee-payroll-list",
    ),
    path(
        "clients/<int:client_pk>/employees/<int:employee_pk>/payroll-records/<int:pk>/",
        payroll_detail,
        name="employee-payroll-detail",
    ),
]
