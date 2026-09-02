from __future__ import annotations

from .models import Permission, Role


def roles_for(user) -> list[Role]:
    """Distinct roles assigned to ``user``, ordered by name."""
    if not user or not getattr(user, "pk", None):
        return []
    return list(Role.objects.filter(user_links__user=user).distinct().order_by("name"))


def permission_codenames_for(user) -> list[str]:
    """Flattened, sorted, de-duplicated permission codenames for ``user``
    (user -> roles -> permissions). See SENTRA_BUILD_SPEC.md §5."""
    if not user or not getattr(user, "pk", None):
        return []
    codenames = (
        Permission.objects.filter(roles__user_links__user=user)
        .values_list("codename", flat=True)
        .distinct()
    )
    return sorted(set(codenames))


def assign_role(user, role, *, assigned_by=None):
    """Idempotently assign ``role`` to ``user``."""
    from .models import UserRole

    obj, created = UserRole.objects.get_or_create(
        user=user,
        role=role,
        defaults={"assigned_by": assigned_by if getattr(assigned_by, "pk", None) else None},
    )
    return obj, created
