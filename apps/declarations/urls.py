from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.declarations.views import (
    ClientDeclarationSubscriptionViewSet,
    DeclarationInstanceViewSet,
    DeclarationTypeViewSet,
)

app_name = "declarations"

router = DefaultRouter()
router.register("declaration-types", DeclarationTypeViewSet, basename="declaration-type")
router.register("declaration-instances", DeclarationInstanceViewSet, basename="declaration-instance")

subscription_list = ClientDeclarationSubscriptionViewSet.as_view({"get": "list", "post": "create"})
subscription_detail = ClientDeclarationSubscriptionViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = router.urls + [
    path(
        "clients/<int:client_pk>/declaration-subscriptions/",
        subscription_list,
        name="client-declaration-subscription-list",
    ),
    path(
        "clients/<int:client_pk>/declaration-subscriptions/<int:pk>/",
        subscription_detail,
        name="client-declaration-subscription-detail",
    ),
]
