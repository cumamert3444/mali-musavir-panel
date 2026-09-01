from django.contrib import admin

from apps.tasks.models import Task, TaskComment


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "office", "client", "status", "priority", "assigned_to", "due_date"]
    list_filter = ["office", "status", "priority"]
    search_fields = ["title", "description"]
    inlines = [TaskCommentInline]
