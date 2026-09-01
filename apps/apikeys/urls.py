from rest_framework.routers import DefaultRouter

from apps.apikeys.views import ApiKeyViewSet

app_name = "apikeys"

router = DefaultRouter()
router.register("keys", ApiKeyViewSet, basename="apikey")

urlpatterns = router.urls
