from django.contrib import admin

from apps.invoicing.models import InvoiceLine, Payment, ServiceInvoice


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(ServiceInvoice)
class ServiceInvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "office", "client", "status", "issue_date", "due_date"]
    list_filter = ["office", "status"]
    search_fields = ["invoice_number", "client__title"]
    inlines = [InvoiceLineInline, PaymentInline]
