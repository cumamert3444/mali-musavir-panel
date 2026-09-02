from django.contrib import admin

from apps.einvoices.models import EInvoiceRecord


@admin.register(EInvoiceRecord)
class EInvoiceRecordAdmin(admin.ModelAdmin):
    list_display = ["client", "doc_type", "direction", "invoice_number", "amount", "issue_date", "status", "office"]
    list_filter = ["doc_type", "direction", "status", "source"]
    search_fields = ["client__title", "invoice_number", "counterparty_title", "counterparty_tax_number"]
