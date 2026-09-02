"""Reusable RBAC enforcement for DRF viewsets (SENTRA_BUILD_SPEC.md §5).

The backend is the single source of truth: every viewset action maps
``self.action -> required permission codename`` and nothing is served on the
default policy alone. The user's full permission set (user -> roles ->
permissions) is resolved *once per request* and memoised on the request object.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission, IsAuthenticated

from .services import permission_codenames_for

_CACHE_ATTR = "_rbac_permission_codenames"


def request_permission_codenames(request) -> set[str]:
    """The requesting user's flattened permission codenames, cached per request."""
    cached = getattr(request, _CACHE_ATTR, None)
    if cached is None:
        user = getattr(request, "user", None)
        cached = set(permission_codenames_for(user)) if user and user.is_authenticated else set()
        setattr(request, _CACHE_ATTR, cached)
    return cached


class _DenyAll(BasePermission):
    """Fail-closed: an action with no codename mapping is never reachable."""

    message = "This action has no permission mapping and is disabled."

    def has_permission(self, request, view):
        return False


def HasPermission(codename: str) -> type[BasePermission]:
    """Build a permission class that requires ``codename``.

    Superusers bypass (Django convention); everyone else must hold the codename
    in their resolved set.
    """

    class _HasPermission(BasePermission):
        message = f"You do not have the required permission: {codename}."

        def has_permission(self, request, view):
            user = getattr(request, "user", None)
            if not (user and user.is_authenticated):
                return False
            if user.is_superuser:
                return True
            return codename in request_permission_codenames(request)

    _HasPermission.__name__ = f"HasPermission_{codename.replace('.', '_')}"
    _HasPermission.__qualname__ = _HasPermission.__name__
    return _HasPermission


class RBACPermissionMixin:
    """Mixin for viewsets: declare ``permission_map = {action: codename}``.

    Every concrete action must appear in the map; an unmapped action is denied
    outright rather than silently falling back to ``IsAuthenticated``.
    """

    permission_map: dict[str, str] = {}

    def get_permissions(self):
        codename = self.permission_map.get(self.action)
        if codename is None:
            return [IsAuthenticated(), _DenyAll()]
        return [IsAuthenticated(), HasPermission(codename)()]
