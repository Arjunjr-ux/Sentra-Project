from datetime import timedelta

import pytest
from django.utils import timezone

from audit.models import AuditLog
from audit.services import write_audit

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(user_factory, as_user):
    return as_user(user_factory(roles=["Admin"]))


def test_audit_list_requires_audit_view(user_factory, as_user):
    manager = as_user(user_factory(roles=["Manager"]))
    assert manager.get("/api/v1/audit-logs/").status_code == 403


def test_audit_list_is_paginated(admin_client):
    resp = admin_client.get("/api/v1/audit-logs/")
    assert resp.status_code == 200
    assert set(resp.data) >= {"count", "next", "previous", "results"}


def test_audit_filters(admin_client, user_factory):
    actor = user_factory(email="filter-actor@example.com")
    old = write_audit(actor=actor, action="user.create")
    AuditLog.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=10))
    write_audit(actor=actor, action="role.update")
    write_audit(actor=None, action="user.create")

    by_action = admin_client.get("/api/v1/audit-logs/?action=user.create")
    assert by_action.data["count"] == 2

    by_actor = admin_client.get(f"/api/v1/audit-logs/?actor={actor.pk}")
    assert by_actor.data["count"] == 2

    since = (timezone.now() - timedelta(days=2)).date().isoformat()
    recent = admin_client.get(f"/api/v1/audit-logs/?date_from={since}")
    actions = {row["action"] for row in recent.data["results"]}
    assert "user.create" in actions and "role.update" in actions
    assert recent.data["count"] == 2  # the 10-day-old row is excluded


def test_audit_search(admin_client, user_factory):
    write_audit(actor=user_factory(email="searchme@example.com"), action="role.delete")
    resp = admin_client.get("/api/v1/audit-logs/?search=searchme")
    assert resp.data["count"] == 1


# --- every mutating endpoint leaves a row (SENTRA_BUILD_SPEC.md §7) --------


def test_mutations_write_audit_rows(admin_client, user_factory):
    target = user_factory()

    admin_client.post(
        "/api/v1/users/",
        {"email": "audited@example.com", "full_name": "A", "password": "Sentra!Pass2026"},
        format="json",
    )
    admin_client.patch(f"/api/v1/users/{target.pk}/", {"full_name": "B"}, format="json")
    admin_client.put(f"/api/v1/users/{target.pk}/roles/", {"role_ids": []}, format="json")
    admin_client.delete(f"/api/v1/users/{target.pk}/")
    admin_client.get("/api/v1/users/export/")

    recorded = set(AuditLog.objects.values_list("action", flat=True))
    assert {
        "user.create",
        "user.update",
        "user.roles.replace",
        "user.deactivate",
        "user.export",
    } <= recorded

    row = AuditLog.objects.filter(action="user.update").latest("created_at")
    assert row.actor is not None
    assert row.ip  # test client sets REMOTE_ADDR
