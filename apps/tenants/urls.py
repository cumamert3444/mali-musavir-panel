from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.tenants.views import (
    AdminUserViewSet,
    MyOfficeView,
    OfficeAdminViewSet,
    PlatformStatsView,
    SubscriptionPlanAdminViewSet,
)

app_name = "tenants"

router = DefaultRouter()
router.register("admin/offices", OfficeAdminViewSet, basename="admin-office")
router.register("admin/users", AdminUserViewSet, basename="admin-user")
router.register("admin/plans", SubscriptionPlanAdminViewSet, basename="admin-plan")

urlpatterns = [
    path("my-office/", MyOfficeView.as_view(), name="my-office"),
    path("admin/stats/", PlatformStatsView.as_view(), name="admin-stats"),
] + router.urls
