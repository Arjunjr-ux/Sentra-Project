"""Root URL configuration.

`/api/v1/auth/*` — plain routes (not a CRUD resource).
`/api/v1/{users,roles,permissions,audit-logs}/` — DRF router; the `/export/`,
`/{id}/roles/`, and `/{id}/permissions/` actions register automatically.
`/api/v1/schema/swagger-ui/` — drf-spectacular.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from accounts.viewsets import UserViewSet
from audit.views import AuditLogViewSet
from rbac.views import PermissionViewSet, RoleViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")
router.register("permissions", PermissionViewSet, basename="permission")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/", include(router.urls)),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
