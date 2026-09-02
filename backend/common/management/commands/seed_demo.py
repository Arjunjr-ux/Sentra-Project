"""Idempotent demo-data seed.

Creates a demo admin / manager / viewer, a handful of extra sample users (mixed
active state and roles), and ~18 audit-log rows spread over the last two weeks so
the app looks populated on first login. Safe to run repeatedly.

The demo password is intentionally shared across all seeded accounts and is
documented in the README (Phase 4).
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from audit.models import AuditLog
from rbac.models import Role, UserRole

User = get_user_model()

DEMO_PASSWORD = "Sentra!Demo2026"  # noqa: S105 - demo fixture, documented in README

# email -> (full_name, role name or None, is_active, is_staff, is_superuser)
DEMO_USERS = [
    ("admin@sentra.dev", "Ada Admin", "Admin", True, True, True),
    ("manager@sentra.dev", "Marcus Manager", "Manager", True, False, False),
    ("viewer@sentra.dev", "Vera Viewer", "Viewer", True, False, False),
    ("alice.morgan@sentra.dev", "Alice Morgan", "Manager", True, False, False),
    ("bob.chen@sentra.dev", "Bob Chen", "Viewer", True, False, False),
    ("carol.diaz@sentra.dev", "Carol Diaz", "Viewer", False, False, False),
    ("dan.wright@sentra.dev", "Dan Wright", "Admin", True, False, False),
    ("erin.patel@sentra.dev", "Erin Patel", "Manager", False, False, False),
    ("frank.olsen@sentra.dev", "Frank Olsen", None, True, False, False),
    ("grace.kim@sentra.dev", "Grace Kim", "Viewer", True, False, False),
]

# (actor email, action, target_type, target_id builder, changes)
AUDIT_TEMPLATES = [
    ("admin@sentra.dev", "auth.login", "", None, {}),
    ("manager@sentra.dev", "auth.login", "", None, {}),
    ("viewer@sentra.dev", "auth.login", "", None, {}),
    (
        "admin@sentra.dev",
        "user.create",
        "User",
        "bob.chen@sentra.dev",
        {"email": "bob.chen@sentra.dev"},
    ),
    (
        "admin@sentra.dev",
        "user.update",
        "User",
        "carol.diaz@sentra.dev",
        {"full_name": ["Carol D", "Carol Diaz"]},
    ),
    (
        "admin@sentra.dev",
        "user.deactivate",
        "User",
        "carol.diaz@sentra.dev",
        {"is_active": [True, False]},
    ),
    (
        "admin@sentra.dev",
        "user.deactivate",
        "User",
        "erin.patel@sentra.dev",
        {"is_active": [True, False]},
    ),
    (
        "dan.wright@sentra.dev",
        "user.roles.replace",
        "User",
        "alice.morgan@sentra.dev",
        {"roles": [["Viewer"], ["Manager"]]},
    ),
    ("admin@sentra.dev", "role.update", "Role", "Manager", {"description": "updated wording"}),
    (
        "admin@sentra.dev",
        "role.permissions.replace",
        "Role",
        "Manager",
        {"added": ["users.delete"]},
    ),
    (
        "manager@sentra.dev",
        "user.create",
        "User",
        "grace.kim@sentra.dev",
        {"email": "grace.kim@sentra.dev"},
    ),
    (
        "manager@sentra.dev",
        "user.update",
        "User",
        "bob.chen@sentra.dev",
        {"full_name": ["Bob C", "Bob Chen"]},
    ),
    ("admin@sentra.dev", "audit.export", "AuditLog", "", {"rows": 42, "format": "xlsx"}),
    ("dan.wright@sentra.dev", "auth.login", "", None, {}),
    ("dan.wright@sentra.dev", "user.export", "User", "", {"rows": 10, "format": "xlsx"}),
    ("admin@sentra.dev", "auth.logout", "", None, {}),
    ("manager@sentra.dev", "auth.logout", "", None, {}),
    ("admin@sentra.dev", "role.create", "Role", "Auditor", {"name": "Auditor"}),
]


class Command(BaseCommand):
    help = "Seed idempotent demo users, role assignments, and audit-log rows."

    @transaction.atomic
    def handle(self, *args, **options):
        roles = {r.name: r for r in Role.objects.all()}
        users: dict[str, User] = {}

        for email, full_name, role_name, is_active, is_staff, is_superuser in DEMO_USERS:
            user, created = User.objects.get_or_create(email=email)
            user.full_name = full_name
            user.is_active = is_active
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.set_password(DEMO_PASSWORD)
            user.save()
            users[email] = user

            if role_name and role_name in roles:
                UserRole.objects.get_or_create(
                    user=user,
                    role=roles[role_name],
                    defaults={"assigned_by": users.get("admin@sentra.dev")},
                )
            verb = "created" if created else "updated"
            self.stdout.write(f"  user {verb}: {email} ({role_name or 'no role'})")

        self._seed_audit(users)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
        self.stdout.write(f"Demo password (all accounts): {DEMO_PASSWORD}")

    def _seed_audit(self, users: dict[str, User]) -> None:
        if AuditLog.objects.exists():
            self.stdout.write("  audit log already populated - skipping audit rows")
            return

        rng = random.Random(20260902)
        now = timezone.now()
        rows = []
        for idx, (actor_email, action, target_type, target_id, changes) in enumerate(
            AUDIT_TEMPLATES
        ):
            rows.append(
                (
                    AuditLog.objects.create(
                        actor=users.get(actor_email),
                        action=action,
                        target_type=target_type,
                        target_id=target_id or "",
                        changes=changes,
                        ip=f"198.51.100.{10 + idx}",
                    ),
                    now
                    - timedelta(
                        days=rng.randint(0, 13),
                        hours=rng.randint(0, 23),
                        minutes=rng.randint(0, 59),
                    ),
                )
            )

        for row, created_at in rows:
            # created_at is auto_now_add; backdate it with an UPDATE that bypasses save().
            AuditLog.objects.filter(pk=row.pk).update(created_at=created_at)

        self.stdout.write(f"  audit rows created: {len(rows)}")
