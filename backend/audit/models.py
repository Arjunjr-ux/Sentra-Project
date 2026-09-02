from django.conf import settings
from django.db import models


class AuditLogError(Exception):
    """Raised on any attempt to mutate or delete an existing audit row."""


class AuditLog(models.Model):
    """Append-only record of every sensitive action (SENTRA_BUILD_SPEC.md §3).

    Rows may be created but never updated or deleted through the ORM. Indexed on
    ``(created_at, actor)`` for the audit-log list view.
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at", "actor"])]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action} by {self.actor_id or 'system'}"

    def save(self, *args, **kwargs):
        if self.pk is not None and AuditLog.objects.filter(pk=self.pk).exists():
            raise AuditLogError("AuditLog rows are append-only and cannot be modified.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AuditLogError("AuditLog rows are append-only and cannot be deleted.")
