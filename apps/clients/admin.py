from django.contrib import admin

from apps.clients.models import (
    Client,
    ClientAssignment,
    ClientContact,
    ClientGroup,
    Contract,
    ServicePackage,
)


class ClientContactInline(admin.TabularInline):
    model = ClientContact
    extra = 0


class ClientAssignmentInline(admin.TabularInline):
    model = ClientAssignment
    extra = 0


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 0


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["title", "office", "status", "legal_type", "tax_number", "monthly_fee", "employee_count"]
    list_filter = ["office", "status", "legal_type", "e_invoice_enabled", "groups"]
    search_fields = ["title", "tax_number", "city"]
    filter_horizontal = ["groups"]
    inlines = [ClientContactInline, ClientAssignmentInline, ContractInline]


@admin.register(ServicePackage)
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ["name", "office", "default_monthly_fee", "is_active"]
    list_filter = ["office", "is_active"]


@admin.register(ClientGroup)
class ClientGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "office", "color"]
    list_filter = ["office"]


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["title", "client", "status", "start_date", "end_date", "auto_renew", "monthly_fee"]
    list_filter = ["status", "auto_renew"]
    search_fields = ["title", "client__title"]
