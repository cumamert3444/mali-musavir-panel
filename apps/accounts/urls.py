from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import MembershipViewSet, MeView, RegisterOfficeView

app_name = "accounts"

router = DefaultRouter()
router.register("members", MembershipViewSet, basename="membership")

urlpatterns = [
    path("register-office/", RegisterOfficeView.as_view(), name="register-office"),
    path("me/", MeView.as_view(), name="me"),
] + router.urls
