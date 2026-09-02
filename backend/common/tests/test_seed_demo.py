import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from audit.models import AuditLog
from common.management.commands.seed_demo import DEMO_USERS
from rbac.services import permission_codenames_for

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    first_users = User.objects.count()
    first_audit = AuditLog.objects.count()

    call_command("seed_demo")

    assert User.objects.count() == first_users == len(DEMO_USERS)
    # Audit rows are append-only and only seeded when the table is empty.
    assert AuditLog.objects.count() == first_audit
    assert 15 <= first_audit <= 20


def test_seed_demo_admin_has_all_permissions():
    call_command("seed_demo")
    admin = User.objects.get(email="admin@sentra.dev")
    assert admin.is_superuser
    assert len(permission_codenames_for(admin)) == 8

    viewer = User.objects.get(email="viewer@sentra.dev")
    assert permission_codenames_for(viewer) == [
        "permissions.view",
        "roles.view",
        "users.view",
    ]

    assert not User.objects.get(email="carol.diaz@sentra.dev").is_active
