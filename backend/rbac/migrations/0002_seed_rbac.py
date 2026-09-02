"""Seed the fixed RBAC catalogue: exactly 8 permissions and 3 system roles
(SENTRA_BUILD_SPEC.md §3). Runs on every fresh database, including Render's
first deploy.
"""

from django.db import migrations

# (codename, description)
PERMISSIONS = [
    ("users.view", "View users"),
    ("users.create", "Create users"),
    ("users.edit", "Edit users"),
    ("users.delete", "Deactivate users"),
    ("roles.view", "View roles and their permissions"),
    ("roles.manage", "Create, edit, and assign roles and permissions"),
    ("permissions.view", "View the permission catalogue"),
    ("audit.view", "View the audit log"),
]

# name -> (description, [permission codenames])
ROLES = {
    "Admin": (
        "Full access to every resource and action.",
        [c for c, _ in PERMISSIONS],
    ),
    "Manager": (
        "Manage users; read-only on roles and permissions.",
        [
            "users.view",
            "users.create",
            "users.edit",
            "users.delete",
            "roles.view",
            "permissions.view",
        ],
    ),
    "Viewer": (
        "Read-only access. Default role assigned on signup.",
        ["users.view", "roles.view", "permissions.view"],
    ),
}


def seed(apps, schema_editor):
    Permission = apps.get_model("rbac", "Permission")
    Role = apps.get_model("rbac", "Role")
    RolePermission = apps.get_model("rbac", "RolePermission")

    perms = {}
    for codename, description in PERMISSIONS:
        perms[codename], _ = Permission.objects.update_or_create(
            codename=codename, defaults={"description": description}
        )

    for name, (description, codenames) in ROLES.items():
        role, _ = Role.objects.update_or_create(
            name=name, defaults={"description": description, "is_system": True}
        )
        wanted = {perms[c].pk for c in codenames}
        existing = set(
            RolePermission.objects.filter(role=role).values_list("permission_id", flat=True)
        )
        for pk in wanted - existing:
            RolePermission.objects.create(role=role, permission_id=pk)
        RolePermission.objects.filter(role=role).exclude(permission_id__in=wanted).delete()


def unseed(apps, schema_editor):
    Permission = apps.get_model("rbac", "Permission")
    Role = apps.get_model("rbac", "Role")

    Role.objects.filter(name__in=ROLES.keys()).delete()
    Permission.objects.filter(codename__in=[c for c, _ in PERMISSIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("rbac", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
