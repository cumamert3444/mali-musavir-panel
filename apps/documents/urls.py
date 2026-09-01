from rest_framework.routers import DefaultRouter

from apps.documents.views import DocumentCategoryViewSet, DocumentViewSet

app_name = "documents"

router = DefaultRouter()
router.register("document-categories", DocumentCategoryViewSet, basename="document-category")
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = router.urls
