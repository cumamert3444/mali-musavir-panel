from rest_framework import viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.documents.models import Document, DocumentCategory
from apps.documents.serializers import DocumentCategorySerializer, DocumentSerializer


class DocumentCategoryViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    search_fields = ["name"]


class DocumentViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Document.objects.select_related("client", "category", "uploaded_by")
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ["client", "category", "declaration_instance"]
    search_fields = ["title", "description"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office, uploaded_by=self.request.user)
        log_action(self.request, action="create", model_name="Document", object_id=instance.id)

    def perform_destroy(self, instance):
        log_action(self.request, action="delete", model_name="Document", object_id=instance.id)
        instance.delete()
