from rest_framework.routers import DefaultRouter

from apps.legal_notices.views import LegalNotificationViewSet

app_name = "legal_notices"

router = DefaultRouter()
router.register("legal-notifications", LegalNotificationViewSet, basename="legal-notification")

urlpatterns = router.urls
