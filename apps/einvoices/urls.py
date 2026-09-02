from rest_framework.routers import DefaultRouter

from apps.einvoices.views import EInvoiceRecordViewSet

app_name = "einvoices"

router = DefaultRouter()
router.register("einvoices", EInvoiceRecordViewSet, basename="einvoice")

urlpatterns = router.urls
