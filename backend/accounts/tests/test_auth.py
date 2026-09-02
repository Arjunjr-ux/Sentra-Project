import pytest
from django.conf import settings

from accounts.serializers import INVALID_CREDENTIALS
from audit.models import AuditLog

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register/"
LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
LOGOUT = "/api/v1/auth/logout/"
ME = "/api/v1/auth/me/"

COOKIE = settings.AUTH_REFRESH_COOKIE
GOOD_PASSWORD = "Sentra!Pass2026"


# --- register ------------------------------------------------------------------


def test_register_creates_user_with_viewer_role(api):
    resp = api.post(
        REGISTER,
        {"email": "New.User@Example.com", "full_name": "New User", "password": GOOD_PASSWORD},
        format="json",
    )

    assert resp.status_code == 201
    assert resp.data["access"]
    assert COOKIE in resp.cookies
    assert resp.cookies[COOKIE]["httponly"]
    assert resp.cookies[COOKIE]["path"] == settings.AUTH_REFRESH_COOKIE_PATH

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    me = api.get(ME)
    assert me.status_code == 200
    assert me.data["email"] == "new.user@example.com"
    assert [r["name"] for r in me.data["roles"]] == ["Viewer"]
    assert me.data["permissions"] == ["permissions.view", "roles.view", "users.view"]
    assert AuditLog.objects.filter(action="auth.register").count() == 1


def test_register_rejects_weak_password(api):
    resp = api.post(
        REGISTER,
        {"email": "weak@example.com", "full_name": "Weak", "password": "123"},
        format="json",
    )
    assert resp.status_code == 400
    assert "password" in resp.data


def test_register_rejects_duplicate_email(api, make_user):
    make_user(email="taken@example.com")
    resp = api.post(
        REGISTER,
        {"email": "taken@example.com", "full_name": "Dup", "password": GOOD_PASSWORD},
        format="json",
    )
    assert resp.status_code == 400


# --- login -------------------------------------------------------------------


def test_login_success(api, make_user):
    make_user(email="ok@example.com", password=GOOD_PASSWORD)
    resp = api.post(LOGIN, {"email": "ok@example.com", "password": GOOD_PASSWORD}, format="json")

    assert resp.status_code == 200
    assert resp.data["access"]
    assert COOKIE in resp.cookies
    assert AuditLog.objects.filter(action="auth.login").count() == 1


@pytest.mark.parametrize(
    "email,password,setup",
    [
        ("ghost@example.com", GOOD_PASSWORD, None),  # unknown email
        ("real@example.com", "wrong-password!!", "active"),  # wrong password
        ("real@example.com", GOOD_PASSWORD, "inactive"),  # inactive account
    ],
)
def test_login_failure_is_generic(api, make_user, email, password, setup):
    if setup == "active":
        make_user(email="real@example.com", password=GOOD_PASSWORD)
    elif setup == "inactive":
        make_user(email="real@example.com", password=GOOD_PASSWORD, is_active=False)

    resp = api.post(LOGIN, {"email": email, "password": password}, format="json")

    assert resp.status_code == 401
    assert resp.data == {"detail": INVALID_CREDENTIALS}
    assert COOKIE not in resp.cookies


def test_login_failure_modes_are_indistinguishable(api, make_user):
    make_user(email="real@example.com", password=GOOD_PASSWORD, is_active=False)

    unknown = api.post(
        LOGIN, {"email": "nobody@example.com", "password": GOOD_PASSWORD}, format="json"
    )
    inactive = api.post(
        LOGIN, {"email": "real@example.com", "password": GOOD_PASSWORD}, format="json"
    )
    wrong = api.post(LOGIN, {"email": "real@example.com", "password": "nope!!!"}, format="json")

    assert unknown.status_code == inactive.status_code == wrong.status_code == 401
    assert unknown.data == inactive.data == wrong.data


# --- me --------------------------------------------------------------------


def test_me_requires_authentication(api):
    assert api.get(ME).status_code == 401


def test_me_returns_flattened_sorted_permissions(auth_client):
    client, _ = auth_client(email="multi@example.com", roles=["Admin", "Viewer"])
    resp = client.get(ME)

    assert resp.status_code == 200
    assert {r["name"] for r in resp.data["roles"]} == {"Admin", "Viewer"}
    assert resp.data["permissions"] == sorted(resp.data["permissions"])
    assert resp.data["permissions"] == [
        "audit.view",
        "permissions.view",
        "roles.manage",
        "roles.view",
        "users.create",
        "users.delete",
        "users.edit",
        "users.view",
    ]


# --- refresh rotation ------------------------------------------------------


def test_refresh_rotates_and_old_token_is_rejected(api, make_user):
    make_user(email="rot@example.com", password=GOOD_PASSWORD)
    login = api.post(LOGIN, {"email": "rot@example.com", "password": GOOD_PASSWORD}, format="json")
    old_refresh = login.cookies[COOKIE].value

    first = api.post(REFRESH)
    assert first.status_code == 200
    assert first.data["access"]
    new_refresh = first.cookies[COOKIE].value
    assert new_refresh != old_refresh

    # Replit the now-rotated (blacklisted) token -> 401.
    api.cookies[COOKIE] = old_refresh
    replay = api.post(REFRESH)
    assert replay.status_code == 401

    # The freshly issued token still works.
    api.cookies[COOKIE] = new_refresh
    assert api.post(REFRESH).status_code == 200


def test_refresh_without_cookie_is_401(api):
    assert api.post(REFRESH).status_code == 401


def test_refresh_with_garbage_cookie_is_401(api):
    api.cookies[COOKIE] = "not-a-real-token"
    assert api.post(REFRESH).status_code == 401


# --- logout --------------------------------------------------------------


def test_logout_without_cookie_returns_204(api):
    resp = api.post(LOGOUT)
    assert resp.status_code == 204


def test_logout_blacklists_and_clears_cookie(api, make_user):
    make_user(email="out@example.com", password=GOOD_PASSWORD)
    api.post(LOGIN, {"email": "out@example.com", "password": GOOD_PASSWORD}, format="json")

    resp = api.post(LOGOUT)
    assert resp.status_code == 204
    assert resp.cookies[COOKIE].value == ""

    # Cookie value is cleared client-side; the token itself is now blacklisted.
    stale = api.post(REFRESH)
    assert stale.status_code == 401


# --- full round trip (SENTRA_BUILD_SPEC.md §12 Phase 1 "done") --------------


def test_login_refresh_logout_roundtrip(api, make_user):
    make_user(email="trip@example.com", password=GOOD_PASSWORD)

    login = api.post(LOGIN, {"email": "trip@example.com", "password": GOOD_PASSWORD}, format="json")
    assert login.status_code == 200
    access = login.data["access"]

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert api.get(ME).status_code == 200

    refresh = api.post(REFRESH)
    assert refresh.status_code == 200
    assert refresh.data["access"]

    api.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.data['access']}")
    assert api.get(ME).status_code == 200

    assert api.post(LOGOUT).status_code == 204
    assert api.post(REFRESH).status_code == 401


# --- throttle (SENTRA_BUILD_SPEC.md §6: 5/min per IP on auth) --------------


def test_login_is_throttled_after_five_attempts(api):
    codes = [
        api.post(
            LOGIN, {"email": "x@example.com", "password": "whatever!!"}, format="json"
        ).status_code
        for _ in range(6)
    ]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429


def test_register_shares_the_auth_throttle_scope(api):
    for i in range(5):
        api.post(
            REGISTER,
            {"email": f"u{i}@example.com", "full_name": "U", "password": GOOD_PASSWORD},
            format="json",
        )
    blocked = api.post(
        REGISTER,
        {"email": "u5@example.com", "full_name": "U", "password": GOOD_PASSWORD},
        format="json",
    )
    assert blocked.status_code == 429
