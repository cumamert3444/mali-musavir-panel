from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.audit import log_action
from apps.core.views import TenantScopedViewSetMixin
from apps.tasks.models import Task, TaskComment
from apps.tasks.serializers import TaskCommentSerializer, TaskSerializer


class TaskViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Task.objects.select_related("client", "assigned_to").prefetch_related("comments__author")
    serializer_class = TaskSerializer
    filterset_fields = ["status", "priority", "assigned_to", "client"]
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "created_at", "priority"]

    def perform_create(self, serializer):
        instance = serializer.save(office=self.request.office, created_by=self.request.user)
        log_action(self.request, action="create", model_name="Task", object_id=instance.id)

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        instance = serializer.save()
        if instance.status == Task.Status.DONE and previous_status != Task.Status.DONE:
            instance.completed_at = timezone.now()
            instance.save(update_fields=["completed_at"])
        log_action(self.request, action="update", model_name="Task", object_id=instance.id)

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        task = self.get_object()
        serializer = TaskCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, author=request.user)
        return Response(TaskCommentSerializer(comment).data, status=201)

    @action(detail=False, methods=["get"])
    def my_tasks(self, request):
        queryset = self.filter_queryset(self.get_queryset()).filter(assigned_to=request.user)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)
