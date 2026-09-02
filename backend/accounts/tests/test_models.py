import pytest
from django.contrib.auth import get_user_model

from audit.models import AuditLog, AuditLogError
from audit.services import write_audit
from rbac.services import permission_codenames_for, roles_for

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_create_user_normalizes_email_and_hashes_password_with_argon2():
    user = User.objects.create_user(email="Person@Example.COM", password="Sentra!Pass2026")
    assert user.email == "Person@example.com"
    assert user.password.startswith("argon2")
    assert user.check_password("Sentra!Pass2026")
    assert not user.is_staff and not user.is_superuser


def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="x")


def test_create_superuser_sets_flags():
    admin = User.objects.create_superuser(
        email="root@example.com", password="Sentra!Pass2026", full_name="Root"
    )
    assert admin.is_staff and admin.is_superuser and admin.is_active
    assert admin.has_perm("anything") and admin.has_module_perms("accounts")


def test_create_superuser_rejects_downgraded_flags():
    with pytest.raises(ValueError):
        User.objects.create_superuser(email="x@example.com", password="p", is_superuser=False)


def test_rbac_helpers_ignore_anonymous_and_unsaved_users():
    assert roles_for(None) == []
    assert permission_codenames_for(User(email="ghost@example.com")) == []


def test_auditlog_is_append_only():
    row = write_audit(actor=None, action="test.event", changes={"a": 1})
    row.action = "tampered"
    with pytest.raises(AuditLogError):
        row.save()
    with pytest.raises(AuditLogError):
        row.delete()
    assert AuditLog.objects.get(pk=row.pk).action == "test.event"
