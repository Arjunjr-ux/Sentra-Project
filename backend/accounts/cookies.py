from django.conf import settings
from rest_framework_simplejwt.settings import api_settings


def set_refresh_cookie(response, refresh_token) -> None:
    """Attach the rotated refresh token as a path-scoped httpOnly cookie."""
    max_age = int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE,
        str(refresh_token),
        max_age=max_age,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )


def clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )
