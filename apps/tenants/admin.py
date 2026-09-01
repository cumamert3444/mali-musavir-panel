from django.contrib import admin

from apps.tenants.models import Office, Subscription, SubscriptionPlan


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("name", "tax_number", "is_active", "api_enabled", "created_at")
    list_filter = ("is_active", "api_enabled")
    search_fields = ("name", "legal_name", "tax_number")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SubscriptionInline]


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price_monthly", "max_users", "max_clients", "api_access_included", "is_active")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("office", "plan", "status", "current_period_end")
    list_filter = ("status", "plan")
