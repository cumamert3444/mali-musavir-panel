from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.tasks.models import Task, TaskComment


class TaskCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ["id", "task", "author", "body", "created_at"]
        read_only_fields = ["id", "task", "author", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_detail = UserSerializer(source="assigned_to", read_only=True)
    client_title = serializers.CharField(source="client.title", read_only=True, default=None)
    comments = TaskCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "client", "client_title", "declaration_instance",
            "title", "description", "status", "priority",
            "assigned_to", "assigned_to_detail", "due_date", "completed_at",
            "comments", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "completed_at", "created_at", "updated_at"]
