from django.contrib import admin

from apps.tax_debts.models import TaxDebtRecord


@admin.register(TaxDebtRecord)
class TaxDebtRecordAdmin(admin.ModelAdmin):
    list_display = ["client", "debt_type", "period_label", "amount", "due_date", "status", "office"]
    list_filter = ["debt_type", "status", "source"]
    search_fields = ["client__title", "description"]
