from django.contrib import admin

from apps.documents.models import Document, DocumentCategory


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "office"]
    list_filter = ["office"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "office", "client", "category", "uploaded_by", "created_at"]
    list_filter = ["office", "category"]
    search_fields = ["title", "description"]
