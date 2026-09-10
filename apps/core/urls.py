from rest_framework.routers import DefaultRouter

from apps.core.views import AccountCodeMemoryViewSet, AuditLogViewSet

app_name = "core"

router = DefaultRouter()
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("account-code-memory", AccountCodeMemoryViewSet, basename="account-code-memory")

urlpatterns = router.urls
