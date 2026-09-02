import pytest

from audit.models import AuditLog
from rbac.models import Permission, Role, RolePermission

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(user_factory, as_user):
    return as_user(user_factory(roles=["Admin"]))


def _codenames(role):
    return sorted(link.permission.codename for link in role.permission_links.all())


def test_create_role_writes_audit(admin_client):
    resp = admin_client.post(
        "/api/v1/roles/", {"name": "Auditor", "description": "read audit"}, format="json"
    )
    assert resp.status_code == 201
    role = Role.objects.get(name="Auditor")
    assert not role.is_system
    entry = AuditLog.objects.get(action="role.create")
    assert entry.target_id == str(role.pk)


def test_system_role_cannot_be_renamed(admin_client):
    admin_role = Role.objects.get(name="Admin")
    resp = admin_client.patch(
        f"/api/v1/roles/{admin_role.pk}/", {"name": "Superuser"}, format="json"
    )
    assert resp.status_code == 400
    assert "rename" in resp.data["detail"].lower()
    admin_role.refresh_from_db()
    assert admin_role.name == "Admin"


def test_system_role_description_can_still_be_edited(admin_client):
    admin_role = Role.objects.get(name="Admin")
    resp = admin_client.patch(
        f"/api/v1/roles/{admin_role.pk}/", {"description": "new copy"}, format="json"
    )
    assert resp.status_code == 200
    admin_role.refresh_from_db()
    assert admin_role.description == "new copy"


def test_system_role_cannot_be_deleted(admin_client):
    admin_role = Role.objects.get(name="Admin")
    resp = admin_client.delete(f"/api/v1/roles/{admin_role.pk}/")
    assert resp.status_code == 400
    assert Role.objects.filter(pk=admin_role.pk).exists()


def test_non_system_role_can_be_deleted(admin_client):
    role = Role.objects.create(name="Temp", description="x")
    resp = admin_client.delete(f"/api/v1/roles/{role.pk}/")
    assert resp.status_code == 204
    assert not Role.objects.filter(pk=role.pk).exists()
    assert AuditLog.objects.filter(action="role.delete", target_id=str(role.pk)).exists()


def test_replace_permissions_is_a_full_replace(admin_client):
    role = Role.objects.create(name="Custom", description="x")
    view = Permission.objects.get(codename="users.view")
    create = Permission.objects.get(codename="users.create")
    edit = Permission.objects.get(codename="users.edit")

    r1 = admin_client.put(
        f"/api/v1/roles/{role.pk}/permissions/",
        {"permission_ids": [view.pk, create.pk]},
        format="json",
    )
    assert r1.status_code == 200
    assert _codenames(role) == ["users.create", "users.view"]

    r2 = admin_client.put(
        f"/api/v1/roles/{role.pk}/permissions/",
        {"permission_ids": [create.pk, edit.pk]},
        format="json",
    )
    assert r2.status_code == 200
    assert _codenames(role) == ["users.create", "users.edit"]
    assert RolePermission.objects.filter(role=role).count() == 2
    assert AuditLog.objects.filter(action="role.permissions.replace").count() == 2


def test_replace_permissions_rejects_unknown_id(admin_client):
    role = Role.objects.create(name="Custom", description="x")
    resp = admin_client.put(
        f"/api/v1/roles/{role.pk}/permissions/",
        {"permission_ids": [999999]},
        format="json",
    )
    assert resp.status_code == 400
    assert "999999" in str(resp.data)


def test_roles_list_is_paginated(admin_client):
    resp = admin_client.get("/api/v1/roles/")
    assert resp.status_code == 200
    assert set(resp.data) >= {"count", "next", "previous", "results"}
    assert resp.data["count"] == 3
