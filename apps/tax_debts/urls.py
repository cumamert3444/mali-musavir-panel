from rest_framework.routers import DefaultRouter

from apps.tax_debts.views import TaxDebtRecordViewSet

app_name = "tax_debts"

router = DefaultRouter()
router.register("tax-debts", TaxDebtRecordViewSet, basename="tax-debt")

urlpatterns = router.urls
