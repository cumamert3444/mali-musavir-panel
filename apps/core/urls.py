from rest_framework.routers import DefaultRouter

from apps.core.views import AuditLogViewSet

app_name = "core"

router = DefaultRouter()
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = router.urls
