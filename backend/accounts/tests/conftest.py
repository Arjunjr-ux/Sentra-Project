import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from rbac.models import Role, UserRole


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """AuthRateThrottle counts live in the default cache; keep tests isolated."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def make_user(django_user_model):
    def _make(email="user@example.com", password="Sentra!Pass2026", roles=(), **extra):
        user = django_user_model.objects.create_user(
            email=email, password=password, full_name=extra.pop("full_name", "Test User"), **extra
        )
        for role_name in roles:
            UserRole.objects.create(user=user, role=Role.objects.get(name=role_name))
        return user

    return _make


@pytest.fixture
def auth_client(api, make_user):
    def _login(**kwargs):
        user = make_user(**kwargs)
        resp = api.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": kwargs.get("password", "Sentra!Pass2026")},
            format="json",
        )
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        return api, user

    return _login
