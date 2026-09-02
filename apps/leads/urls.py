from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.leads.views import DemoRequestAdminViewSet, DemoRequestCreateView

app_name = "leads"

router = DefaultRouter()
router.register("admin/leads", DemoRequestAdminViewSet, basename="admin-lead")

urlpatterns = [
    path("leads/demo-request/", DemoRequestCreateView.as_view(), name="demo-request"),
] + router.urls
