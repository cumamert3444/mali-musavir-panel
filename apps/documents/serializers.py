from rest_framework import serializers

from apps.documents.models import Document, DocumentCategory


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = ["id", "name"]


class DocumentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True, default=None)

    class Meta:
        model = Document
        fields = [
            "id", "client", "category", "category_name", "declaration_instance",
            "title", "file", "description", "uploaded_by_email", "created_at",
        ]
        read_only_fields = ["id", "uploaded_by_email", "created_at"]
