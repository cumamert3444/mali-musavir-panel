from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import Membership, User


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    inlines = [MembershipInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Kisisel Bilgiler", {"fields": ("first_name", "last_name", "phone")}),
        ("Yetkiler", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Onemli Tarihler", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    readonly_fields = ["date_joined"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "office", "role", "is_active"]
    list_filter = ["role", "is_active", "office"]
    search_fields = ["user__email", "office__name"]
