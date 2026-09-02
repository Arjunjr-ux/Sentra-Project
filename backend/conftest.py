"""Project-wide pytest fixtures (available to every test package)."""

from uuid import uuid4

import pytest
from django.core.cache import cache

DEFAULT_TEST_PASSWORD = "Sentra!Pass2026"


@pytest.fixture(autouse=True)
def _reset_caches():
    """Throttle counters and permission caches live in the default cache."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def drf_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def user_factory(db, django_user_model):
    from rbac.models import Role, UserRole

    def _make(email=None, *, roles=(), password=DEFAULT_TEST_PASSWORD, **extra):
        email = email or f"user-{uuid4().hex[:10]}@example.com"
        user = django_user_model.objects.create_user(
            email=email,
            password=password,
            full_name=extra.pop("full_name", "Test User"),
            **extra,
        )
        for role_name in roles:
            UserRole.objects.get_or_create(user=user, role=Role.objects.get(name=role_name))
        return user

    return _make


@pytest.fixture
def as_user():
    """Return an APIClient carrying a Bearer access token for ``user`` — bypasses
    the login endpoint (and its throttle) entirely."""
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    def _as(user):
        client = APIClient()
        token = RefreshToken.for_user(user).access_token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return _as
