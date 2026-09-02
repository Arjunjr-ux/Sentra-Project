from __future__ import annotations

from .models import AuditLog


def write_audit(
    *,
    actor=None,
    action: str,
    target=None,
    target_type: str = "",
    target_id: str = "",
    changes: dict | None = None,
    ip: str | None = None,
) -> AuditLog:
    """Append a single audit row.

    ``target`` is a convenience: if given, ``target_type`` / ``target_id`` are
    derived from it unless explicitly passed.
    """

    if target is not None:
        target_type = target_type or target.__class__.__name__
        target_id = target_id or str(getattr(target, "pk", ""))

    return AuditLog.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        changes=changes or {},
        ip=ip,
    )
