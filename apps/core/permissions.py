from rest_framework.permissions import BasePermission

from apps.accounts.models import Membership


class HasActiveOffice(BasePermission):
    """`request.office` çözümlenmiş olmalı (bkz. apps.core.views mixin'i)."""

    message = "Aktif bir ofis bulunamadı. X-Office-Id header'ı ile bir ofis seçin."

    def has_permission(self, request, view):
        return getattr(request, "office", None) is not None


class HasOfficeRole(BasePermission):
    """Belirli rollerle sınırlı endpoint'ler için kullanılır.

    View üzerinde `required_roles = [Membership.Role.OWNER, ...]` tanımlanmalı.
    Tanımlı değilse (None/boş) sadece ofis üyeliği yeterli sayılır.
    """

    message = "Bu işlem için yetkiniz yok."

    def has_permission(self, request, view):
        required_roles = getattr(view, "required_roles", None)
        if not required_roles:
            return True
        if getattr(request.user, "is_superuser", False):
            return True
        office = getattr(request, "office", None)
        if office is None:
            return False
        return Membership.objects.filter(
            user=request.user, office=office, is_active=True, role__in=required_roles
        ).exists()
