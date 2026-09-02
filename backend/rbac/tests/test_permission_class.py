import pytest

from accounts.viewsets import UserViewSet
from audit.views import AuditLogViewSet
from rbac.permissions import (
    RBACPermissionMixin,
    _DenyAll,
    request_permission_codenames,
)
from rbac.views import PermissionViewSet, RoleViewSet

pytestmark = pytest.mark.django_db

STANDARD_ACTIONS = ["list", "retrieve", "create", "update", "partial_update", "destroy"]


def test_permission_set_is_resolved_once_per_request(rf, user_factory, django_assert_num_queries):
    user = user_factory(roles=["Admin"])
    request = rf.get("/api/v1/users/")
    request.user = user

    with django_assert_num_queries(1):
        first = request_permission_codenames(request)
        second = request_permission_codenames(request)

    assert first is second
    assert "users.view" in first


def test_anonymous_request_resolves_to_empty_set(rf):
    from django.contrib.auth.models import AnonymousUser

    request = rf.get("/api/v1/users/")
    request.user = AnonymousUser()
    assert request_permission_codenames(request) == set()


def test_unmapped_action_is_denied():
    class Dummy(RBACPermissionMixin):
        permission_map = {"list": "users.view"}

    view = Dummy()
    view.action = "some_unmapped_action"
    assert any(isinstance(perm, _DenyAll) for perm in view.get_permissions())


@pytest.mark.parametrize("viewset", [UserViewSet, RoleViewSet, PermissionViewSet, AuditLogViewSet])
def test_every_concrete_action_has_a_codename(viewset):
    mapped = set(viewset.permission_map)

    present = {name for name in STANDARD_ACTIONS if hasattr(viewset, name)}
    present |= {extra.__name__ for extra in viewset.get_extra_actions()}

    missing = present - mapped
    assert not missing, f"{viewset.__name__} actions with no permission codename: {missing}"
