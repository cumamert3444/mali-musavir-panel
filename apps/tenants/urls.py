from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.tenants.views import MyOfficeView, OfficeAdminViewSet

app_name = "tenants"

router = DefaultRouter()
router.register("admin/offices", OfficeAdminViewSet, basename="admin-office")

urlpatterns = [
    path("my-office/", MyOfficeView.as_view(), name="my-office"),
] + router.urls
