from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.invoicing.views import ClientAccountStatementView, PaymentViewSet, ServiceInvoiceViewSet

app_name = "invoicing"

router = DefaultRouter()
router.register("invoices", ServiceInvoiceViewSet, basename="invoice")

payment_list = PaymentViewSet.as_view({"get": "list", "post": "create"})
payment_detail = PaymentViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = router.urls + [
    path("invoices/<int:invoice_pk>/payments/", payment_list, name="invoice-payment-list"),
    path("invoices/<int:invoice_pk>/payments/<int:pk>/", payment_detail, name="invoice-payment-detail"),
    path(
        "clients/<int:client_pk>/account-statement/",
        ClientAccountStatementView.as_view(),
        name="client-account-statement",
    ),
]
