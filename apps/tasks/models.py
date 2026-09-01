from django.conf import settings
from django.db import models

from apps.clients.models import Client
from apps.core.mixins import TenantScopedModel
from apps.core.models import TimeStampedModel
from apps.declarations.models import DeclarationInstance


class Task(TenantScopedModel, TimeStampedModel):
    """Ofis ici gorev/kanban karti. Bir musteriye ve/veya bir beyanname
    kaydina baglanabilir (ornek: 'ABC Ltd - Agustos KDV'yi hazirla')."""

    class Status(models.TextChoices):
        TODO = "todo", "Yapilacak"
        IN_PROGRESS = "in_progress", "Devam Ediyor"
        REVIEW = "review", "Kontrol Bekliyor"
        DONE = "done", "Tamamlandi"

    class Priority(models.TextChoices):
        LOW = "low", "Dusuk"
        NORMAL = "normal", "Normal"
        HIGH = "high", "Yuksek"
        URGENT = "urgent", "Acil"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True)
    declaration_instance = models.ForeignKey(
        DeclarationInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "due_date"]
        indexes = [models.Index(fields=["office", "status", "assigned_to"])]

    def __str__(self) -> str:
        return self.title


class TaskComment(TimeStampedModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    body = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Yorum #{self.pk} - {self.task}"
