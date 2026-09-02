"""The permission matrix — "the test that matters" (SENTRA_BUILD_SPEC.md §7).

Every seed role (Admin / Manager / Viewer) plus a no-role user, against a
representative endpoint from each resource, asserting the exact status code the
§3 permission sets imply.
"""

from uuid import uuid4

import pytest

from rbac.models import Role

pytestmark = pytest.mark.django_db

ROLE_TO_SEED = {
    "admin": ["Admin"],
    "manager": ["Manager"],
    "viewer": ["Viewer"],
    "norole": [],
}

# spec  ->  {role: expected status}. Ordered so destructive rows run last.
MATRIX = {
    "GET /users/": {"admin": 200, "manager": 200, "viewer": 200, "norole": 403},
    "POST /users/": {"admin": 201, "manager": 201, "viewer": 403, "norole": 403},
    "PATCH /users/{uid}/": {"admin": 200, "manager": 200, "viewer": 403, "norole": 403},
    "GET /roles/": {"admin": 200, "manager": 200, "viewer": 200, "norole": 403},
    "POST /roles/": {"admin": 201, "manager": 403, "viewer": 403, "norole": 403},
    "PATCH /roles/{rid}/": {"admin": 200, "manager": 403, "viewer": 403, "norole": 403},
    "PUT /roles/{rid}/permissions/": {
        "admin": 200,
        "manager": 403,
        "viewer": 403,
        "norole": 403,
    },
    "PUT /users/{uid}/roles/": {
        "admin": 200,
        "manager": 403,
        "viewer": 403,
        "norole": 403,
    },
    "GET /permissions/": {"admin": 200, "manager": 200, "viewer": 200, "norole": 403},
    "GET /audit-logs/": {"admin": 200, "manager": 403, "viewer": 403, "norole": 403},
    "GET /users/export/": {"admin": 200, "manager": 200, "viewer": 200, "norole": 403},
    "GET /roles/export/": {"admin": 200, "manager": 200, "viewer": 200, "norole": 403},
    "GET /audit-logs/export/": {
        "admin": 200,
        "manager": 403,
        "viewer": 403,
        "norole": 403,
    },
    "DELETE /users/{uid}/": {"admin": 204, "manager": 204, "viewer": 403, "norole": 403},
    "DELETE /roles/{rid}/": {"admin": 204, "manager": 403, "viewer": 403, "norole": 403},
}


def _body(spec):
    return {
        "POST /users/": {
            "email": f"matrix-{uuid4().hex[:8]}@example.com",
            "full_name": "Matrix",
            "password": "Sentra!Pass2026",
        },
        "PATCH /users/{uid}/": {"full_name": "Changed"},
        "POST /roles/": {"name": f"Matrix-{uuid4().hex[:6]}", "description": "d"},
        "PATCH /roles/{rid}/": {"description": "changed"},
        "PUT /roles/{rid}/permissions/": {"permission_ids": []},
        "PUT /users/{uid}/roles/": {"role_ids": []},
    }.get(spec, {})


@pytest.mark.parametrize("role", list(ROLE_TO_SEED))
def test_permission_matrix(role, user_factory, as_user):
    actor = user_factory(roles=ROLE_TO_SEED[role])
    client = as_user(actor)

    target_user = user_factory()
    temp_role = Role.objects.create(name=f"Temp-{uuid4().hex[:6]}", description="temp")
    ctx = {"uid": target_user.id, "rid": temp_role.id}

    for spec, expected in MATRIX.items():
        method, path_tpl = spec.split(" ", 1)
        path = "/api/v1/" + path_tpl.format(**ctx).lstrip("/")
        resp = getattr(client, method.lower())(path, _body(spec), format="json")
        assert resp.status_code == expected[role], (
            f"{spec} as {role}: got {resp.status_code}, expected {expected[role]} "
            f"({getattr(resp, 'data', None)})"
        )


def test_unauthenticated_requests_are_rejected(drf_client):
    for path in ("/api/v1/users/", "/api/v1/roles/", "/api/v1/permissions/", "/api/v1/audit-logs/"):
        assert drf_client.get(path).status_code == 401
