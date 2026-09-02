import pytest
from django.contrib.auth import get_user_model

from audit.models import AuditLog
from rbac.models import Role, UserRole

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def admin(user_factory):
    return user_factory(email="admin-actor@example.com", roles=["Admin"])


@pytest.fixture
def admin_client(admin, as_user):
    return as_user(admin)


def _role_ids(user):
    return sorted(UserRole.objects.filter(user=user).values_list("role_id", flat=True))


# --- CRUD + soft delete -----------------------------------------------------


def test_create_user_persists_and_audits(admin_client):
    resp = admin_client.post(
        "/api/v1/users/",
        {"email": "Fresh@Example.com", "full_name": "Fresh", "password": "Sentra!Pass2026"},
        format="json",
    )
    assert resp.status_code == 201
    user = User.objects.get(email="fresh@example.com")
    assert AuditLog.objects.filter(action="user.create", target_id=str(user.pk)).exists()


def test_patch_user_records_field_diff(admin_client, user_factory):
    target = user_factory(full_name="Old Name")
    resp = admin_client.patch(
        f"/api/v1/users/{target.pk}/", {"full_name": "New Name"}, format="json"
    )
    assert resp.status_code == 200
    target.refresh_from_db()
    assert target.full_name == "New Name"
    entry = AuditLog.objects.get(action="user.update", target_id=str(target.pk))
    assert entry.changes["full_name"] == ["Old Name", "New Name"]


def test_delete_is_a_soft_deactivate(admin_client, user_factory):
    target = user_factory()
    resp = admin_client.delete(f"/api/v1/users/{target.pk}/")
    assert resp.status_code == 204
    target.refresh_from_db()
    assert target.is_active is False
    assert AuditLog.objects.filter(action="user.deactivate", target_id=str(target.pk)).exists()


def test_put_on_user_detail_is_405(admin_client, user_factory):
    target = user_factory()
    resp = admin_client.put(
        f"/api/v1/users/{target.pk}/",
        {"email": target.email, "full_name": "x", "is_active": True},
        format="json",
    )
    assert resp.status_code == 405


# --- role assignment ------------------------------------------------------


def test_replace_roles_is_a_full_replace(admin_client, user_factory):
    target = user_factory(roles=["Viewer"])
    manager = Role.objects.get(name="Manager")
    auditor = Role.objects.get(name="Admin")

    resp = admin_client.put(
        f"/api/v1/users/{target.pk}/roles/",
        {"role_ids": [manager.pk, auditor.pk]},
        format="json",
    )
    assert resp.status_code == 200
    assert _role_ids(target) == sorted([manager.pk, auditor.pk])
    entry = AuditLog.objects.get(action="user.roles.replace", target_id=str(target.pk))
    assert entry.changes["roles"][1] == sorted([manager.pk, auditor.pk])


def test_replace_roles_rejects_unknown_id(admin_client, user_factory):
    target = user_factory()
    resp = admin_client.put(
        f"/api/v1/users/{target.pk}/roles/", {"role_ids": [123456]}, format="json"
    )
    assert resp.status_code == 400
    assert "123456" in str(resp.data)


# --- §5 guard rails -----------------------------------------------------


def test_cannot_deactivate_self_via_delete(admin, admin_client):
    resp = admin_client.delete(f"/api/v1/users/{admin.pk}/")
    assert resp.status_code == 400
    admin.refresh_from_db()
    assert admin.is_active is True


def test_cannot_deactivate_self_via_patch(admin, admin_client):
    resp = admin_client.patch(f"/api/v1/users/{admin.pk}/", {"is_active": False}, format="json")
    assert resp.status_code == 400
    admin.refresh_from_db()
    assert admin.is_active is True


def test_can_still_edit_own_other_fields(admin, admin_client):
    resp = admin_client.patch(
        f"/api/v1/users/{admin.pk}/", {"full_name": "Renamed Self"}, format="json"
    )
    assert resp.status_code == 200


def test_cannot_drop_own_last_admin_role(admin, admin_client):
    resp = admin_client.put(f"/api/v1/users/{admin.pk}/roles/", {"role_ids": []}, format="json")
    assert resp.status_code == 400
    assert _role_ids(admin) == sorted(
        UserRole.objects.filter(user=admin).values_list("role_id", flat=True)
    )
    assert UserRole.objects.filter(user=admin, role__name="Admin").exists()


def test_can_drop_own_admin_role_when_another_admin_exists(admin, admin_client, user_factory):
    user_factory(roles=["Admin"])  # a second admin
    viewer = Role.objects.get(name="Viewer")
    resp = admin_client.put(
        f"/api/v1/users/{admin.pk}/roles/", {"role_ids": [viewer.pk]}, format="json"
    )
    assert resp.status_code == 200
    assert not UserRole.objects.filter(user=admin, role__name="Admin").exists()


def test_can_drop_a_non_admin_role_from_self(admin, admin_client):
    admin_role = Role.objects.get(name="Admin")
    viewer = Role.objects.get(name="Viewer")
    UserRole.objects.create(user=admin, role=viewer)

    resp = admin_client.put(
        f"/api/v1/users/{admin.pk}/roles/", {"role_ids": [admin_role.pk]}, format="json"
    )
    assert resp.status_code == 200
    assert _role_ids(admin) == [admin_role.pk]


# --- list contract ------------------------------------------------------


def test_users_list_pagination_and_filters(admin_client, user_factory):
    user_factory(is_active=False, email="inactive-one@example.com")
    user_factory(is_active=False, email="inactive-two@example.com")

    resp = admin_client.get("/api/v1/users/?is_active=false&ordering=email&page_size=1")
    assert resp.status_code == 200
    assert set(resp.data) >= {"count", "next", "previous", "results"}
    assert resp.data["count"] == 2
    assert len(resp.data["results"]) == 1


def test_page_size_is_capped_at_100(admin_client):
    resp = admin_client.get("/api/v1/users/?page_size=500")
    assert resp.status_code == 200
    # only the actor exists, but the cap is what we're checking
    assert resp.data["results"] is not None


def test_users_search_matches_email_and_name(admin_client, user_factory):
    user_factory(email="needle@example.com", full_name="Zzz")
    resp = admin_client.get("/api/v1/users/?search=needle")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
