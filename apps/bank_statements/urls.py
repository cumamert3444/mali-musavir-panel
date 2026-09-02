from rest_framework.routers import DefaultRouter

from apps.bank_statements.views import BankStatementImportViewSet, BankTransactionViewSet

app_name = "bank_statements"

router = DefaultRouter()
router.register("bank-statements", BankStatementImportViewSet, basename="bank-statement")
router.register("bank-transactions", BankTransactionViewSet, basename="bank-transaction")

urlpatterns = router.urls
