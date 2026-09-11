"""
Django settings for the Sentra backend.

Phase 0 scaffold: environment-driven configuration wired up (python-dotenv +
dj-database-url), the core DRF / spectacular / CORS apps registered, whitenoise
for static files. Application models, auth, and RBAC land in later phases.

Docs: https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env if present (never committed). Real deploys inject real env vars.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def as_origin(value: str) -> str:
    """Normalise an origin: drop a trailing slash, and assume https:// when the
    scheme is missing. Render's blueprint can only pass a bare hostname via
    `fromService`, but CORS/CSRF need a full scheme-qualified origin."""
    value = value.strip().rstrip("/")
    if value and "://" not in value:
        value = f"https://{value}"
    return value


# --- Core -------------------------------------------------------------------

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-dev-only-key-replace-me-in-any-real-environment",
)

DEBUG = env_bool("DEBUG", True)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")


# --- Applications ----------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    # Local
    "accounts",
    "rbac",
    "audit",
    "common",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --- Database ------------------------------------------------------------------
# SQLite locally; DATABASE_URL (e.g. Postgres on Render) overrides in deploys.

DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# --- Password hashing & validation ----------------------------------------

# Argon2 first (see SENTRA_BUILD_SPEC.md §6). The remaining hashers stay listed
# so pre-existing hashes still verify and get upgraded on next login.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalization -------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# --- Static files -------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Django REST Framework ---------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # JWT only: the access token is a Bearer header, the refresh token rides an
    # httpOnly cookie. No SessionAuthentication → no accidental CSRF coupling on
    # the /auth/ endpoints.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Nothing is public unless it explicitly opts out (SENTRA_BUILD_SPEC.md §5).
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # register/ and login/ attach common.throttling.AuthRateThrottle explicitly;
    # this is the dedicated "auth" scope from §6, not the general anon rate.
    "DEFAULT_THROTTLE_RATES": {
        "auth": "5/min",
    },
    "DEFAULT_PAGINATION_CLASS": "common.pagination.DefaultPagination",
    # Guarantees a stable `detail` key on every error response (§4).
    "EXCEPTION_HANDLER": "common.exceptions.sentra_exception_handler",
}

# Hard cap on rows written by any /export/ endpoint (§4). Overridable in tests.
EXPORT_MAX_ROWS = 10_000

# --- SimpleJWT -------------------------------------------------------------

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Refresh-token cookie. Path-scoped to the auth endpoints so it is never sent to
# the rest of the API. SameSite=None requires Secure, which we only enable
# outside DEBUG so local http dev keeps working (SENTRA_BUILD_SPEC.md §5).
AUTH_REFRESH_COOKIE = "refresh_token"
AUTH_REFRESH_COOKIE_PATH = "/api/v1/auth/"
AUTH_REFRESH_COOKIE_SECURE = not DEBUG
AUTH_REFRESH_COOKIE_SAMESITE = "Lax" if DEBUG else "None"

SPECTACULAR_SETTINGS = {
    "TITLE": "Sentra API",
    "DESCRIPTION": "Access-management console — users, roles, permissions, audit log.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1",
    # The OpenAPI schema and Swagger UI are public (no data, standard practice) —
    # keep them reachable despite the IsAuthenticated default. The deploy health
    # check hits /api/v1/schema/.
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
}


# --- CORS / CSRF ----------------------------------------------------------

# Strict allow-list: the frontend origin only, with credentials so the httpOnly
# refresh cookie is accepted (SENTRA_BUILD_SPEC.md §6).
CORS_ALLOWED_ORIGINS = [
    as_origin(o) for o in env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    as_origin(o) for o in env_list("CSRF_TRUSTED_ORIGINS", ",".join(CORS_ALLOWED_ORIGINS))
]


# --- Security headers -----------------------------------------------------
# Always-on hardening; the TLS-dependent switches turn on when DEBUG is False.
# Verify with: DEBUG=False python manage.py check --deploy

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
# Render (and most PaaS) terminate TLS at the edge and forward this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31_536_000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
