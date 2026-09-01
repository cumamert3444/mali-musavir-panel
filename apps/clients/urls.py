from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.clients.views import (
    ClientAssignmentViewSet,
    ClientContactViewSet,
    ClientGroupViewSet,
    ClientViewSet,
    ContractViewSet,
    ServicePackageViewSet,
)

app_name = "clients"

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")
router.register("service-packages", ServicePackageViewSet, basename="service-package")
router.register("client-groups", ClientGroupViewSet, basename="client-group")

contact_list = ClientContactViewSet.as_view({"get": "list", "post": "create"})
contact_detail = ClientContactViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
assignment_list = ClientAssignmentViewSet.as_view({"get": "list", "post": "create"})
assignment_detail = ClientAssignmentViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
contract_list = ContractViewSet.as_view({"get": "list", "post": "create"})
contract_detail = ContractViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = router.urls + [
    path("clients/<int:client_pk>/contacts/", contact_list, name="client-contact-list"),
    path("clients/<int:client_pk>/contacts/<int:pk>/", contact_detail, name="client-contact-detail"),
    path("clients/<int:client_pk>/assignments/", assignment_list, name="client-assignment-list"),
    path("clients/<int:client_pk>/assignments/<int:pk>/", assignment_detail, name="client-assignment-detail"),
    path("clients/<int:client_pk>/contracts/", contract_list, name="client-contract-list"),
    path("clients/<int:client_pk>/contracts/<int:pk>/", contract_detail, name="client-contract-detail"),
]
