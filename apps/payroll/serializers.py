from rest_framework import serializers

from apps.payroll.models import Employee, PayrollRecord


class PayrollRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollRecord
        fields = [
            "id", "employee", "period_label",
            "gross_salary", "sgk_employee_share", "sgk_employer_share",
            "income_tax", "stamp_tax", "net_salary", "employer_cost",
            "status", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "employee", "created_at", "updated_at"]


class EmployeeSerializer(serializers.ModelSerializer):
    payroll_records = PayrollRecordSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "client", "full_name", "tc_no", "sgk_sicil_no", "position",
            "employment_type", "status", "hire_date", "termination_date",
            "gross_salary", "minimum_wage_support", "notes",
            "sgk_entry_notified", "sgk_entry_notified_at", "sgk_exit_notified", "sgk_exit_notified_at",
            "payroll_records", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "client", "created_at", "updated_at",
            "sgk_entry_notified_at", "sgk_exit_notified_at",
        ]
