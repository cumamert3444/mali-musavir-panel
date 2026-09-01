"""Denetim kaydi (AuditLog) olusturmak icin tek merkez fonksiyon."""
from __future__ import annotations

from typing import Optional


def log_action(
    request=None,
    *,
    action: str = "other",
    office=None,
    actor=None,
    model_name: str = "",
    object_id: str = "",
    metadata: Optional[dict] = None,
) -> None:
    from apps.core.models import AuditLog

    if request is not None:
        office = office or getattr(request, "office", None)
        actor = actor or getattr(request, "user", None)
        if actor is not None and not getattr(actor, "is_authenticated", False):
            actor = None
        method = getattr(request, "method", "")
        path = getattr(request, "path", "")
        ip_address = getattr(request, "client_ip", None) or request.META.get("REMOTE_ADDR")
    else:
        method = ""
        path = ""
        ip_address = None

    AuditLog.objects.create(
        office=office,
        actor=actor,
        actor_label=getattr(actor, "email", "") if actor else "",
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else "",
        method=method,
        path=path,
        ip_address=ip_address,
        metadata=metadata or {},
    )
