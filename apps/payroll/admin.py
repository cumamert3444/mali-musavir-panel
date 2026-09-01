from django.contrib import admin

from apps.payroll.models import Employee, PayrollRecord


class PayrollRecordInline(admin.TabularInline):
    model = PayrollRecord
    extra = 0


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["full_name", "client", "position", "status", "hire_date", "termination_date"]
    list_filter = ["status", "employment_type"]
    search_fields = ["full_name", "tc_no", "sgk_sicil_no", "client__title"]
    inlines = [PayrollRecordInline]


@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ["employee", "period_label", "gross_salary", "net_salary", "status"]
    list_filter = ["status"]
    search_fields = ["employee__full_name"]
