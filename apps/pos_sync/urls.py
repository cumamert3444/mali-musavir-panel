from rest_framework.routers import DefaultRouter

from apps.pos_sync.views import DailyPosReportViewSet

app_name = "pos_sync"

router = DefaultRouter()
router.register("pos-reports", DailyPosReportViewSet, basename="pos-report")

urlpatterns = router.urls
