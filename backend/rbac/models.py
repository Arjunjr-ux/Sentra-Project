from django.conf import settings
from django.db import models


class Permission(models.Model):
    """A single `resource.action` capability. Catalogue is seeded by migration
    and read-only via the API (SENTRA_BUILD_SPEC.md §3)."""

    codename = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["codename"]

    def __str__(self):
        return self.codename


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    permissions = models.ManyToManyField(
        Permission,
        through="RolePermission",
        related_name="roles",
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """M2M through-table for Role <-> Permission."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permission_links")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_links")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "permission"], name="uniq_role_permission")
        ]

    def __str__(self):
        return f"{self.role} -> {self.permission}"


class UserRole(models.Model):
    """Assignment of a Role to a User, keeping who-assigned-it for the audit
    trail (SENTRA_BUILD_SPEC.md §3)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_links"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_links")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="roles_assigned",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assigned_at"]
        constraints = [models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")]

    def __str__(self):
        return f"{self.user} -> {self.role}"
