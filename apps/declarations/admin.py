from django.contrib import admin

from apps.declarations.models import ClientDeclarationSubscription, DeclarationInstance, DeclarationType


@admin.register(DeclarationType)
class DeclarationTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "office", "code", "period", "due_month_offset", "due_day", "is_active"]
    list_filter = ["office", "period", "is_active"]
    search_fields = ["name", "code"]


@admin.register(ClientDeclarationSubscription)
class ClientDeclarationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["client", "declaration_type", "is_active", "starts_on"]
    list_filter = ["is_active", "declaration_type"]
    search_fields = ["client__title"]


@admin.register(DeclarationInstance)
class DeclarationInstanceAdmin(admin.ModelAdmin):
    list_display = ["client", "declaration_type", "period_label", "due_date", "status"]
    list_filter = ["office", "status", "declaration_type"]
    search_fields = ["client__title", "period_label"]
    date_hierarchy = "due_date"
