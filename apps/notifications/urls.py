from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.notifications.views import DispatchStatementView, NotificationViewSet

app_name = "notifications"

router = DefaultRouter()
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("notifications/dispatch-statement/", DispatchStatementView.as_view(), name="dispatch-statement"),
] + router.urls
