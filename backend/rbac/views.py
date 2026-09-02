from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.response import Response

from common.exports import build_xlsx_response
from common.mixins import AuditMixin
from common.utils import echo_filter_params

from .filters import RoleFilter
from .models import Permission, Role, RolePermission
from .permissions import RBACPermissionMixin
from .serializers import (
    PermissionSerializer,
    RolePermissionsReplaceSerializer,
    RoleSerializer,
    RoleWriteSerializer,
)

_ROLE_PREFETCH = "permission_links__permission"


class RoleViewSet(RBACPermissionMixin, AuditMixin, viewsets.ModelViewSet):
    """Role CRUD. System roles are rename/delete-protected (SENTRA_BUILD_SPEC.md
    §5); their permission sets may still be edited."""

    queryset = Role.objects.all().prefetch_related(_ROLE_PREFETCH)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RoleFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    permission_map = {
        "list": "roles.view",
        "retrieve": "roles.view",
        "create": "roles.manage",
        "update": "roles.manage",
        "partial_update": "roles.manage",
        "destroy": "roles.manage",
        "replace_permissions": "roles.manage",
        "export": "roles.view",
    }

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return RoleWriteSerializer
        if self.action == "replace_permissions":
            return RolePermissionsReplaceSerializer
        return RoleSerializer

    def perform_create(self, serializer):
        role = serializer.save()
        self.audit(
            "role.create",
            target=role,
            changes={"name": role.name, "description": role.description},
        )

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        if not kwargs.get("partial", False):
            raise MethodNotAllowed(request.method)
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        role = serializer.instance
        new_name = serializer.validated_data.get("name")
        if role.is_system and new_name is not None and new_name != role.name:
            raise ValidationError("System roles cannot be renamed.")

        tracked = ["name", "description"]
        before = {field: getattr(role, field) for field in tracked}
        role = serializer.save()
        changes = {
            field: [before[field], getattr(role, field)]
            for field in tracked
            if before[field] != getattr(role, field)
        }
        self.audit("role.update", target=role, changes=changes)

    def perform_destroy(self, instance):
        if instance.is_system:
            raise ValidationError("System roles cannot be deleted.")
        self.audit(
            "role.delete",
            target_type="Role",
            target_id=str(instance.pk),
            changes={"name": instance.name},
        )
        instance.delete()

    @extend_schema(request=RolePermissionsReplaceSerializer, responses={200: RoleSerializer})
    @action(detail=True, methods=["put"], url_path="permissions")
    def replace_permissions(self, request, pk=None):
        role = self.get_object()
        serializer = RolePermissionsReplaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_perms = serializer.validated_data["permission_ids"]
        new_ids = {perm.pk for perm in new_perms}
        old_ids = set(
            RolePermission.objects.filter(role=role).values_list("permission_id", flat=True)
        )

        with transaction.atomic():
            RolePermission.objects.filter(role=role, permission_id__in=old_ids - new_ids).delete()
            RolePermission.objects.bulk_create(
                RolePermission(role=role, permission=perm)
                for perm in new_perms
                if perm.pk not in old_ids
            )

        self.audit(
            "role.permissions.replace",
            target=role,
            changes={"permissions": [sorted(old_ids), sorted(new_ids)]},
        )
        fresh = self.get_queryset().get(pk=role.pk)
        return Response(RoleSerializer(fresh).data)

    @extend_schema(responses={200: OpenApiResponse(description="An .xlsx file")})
    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        response, count = build_xlsx_response(
            filename="roles.xlsx",
            headers=[
                "ID",
                "Name",
                "Description",
                "System",
                "Permission count",
                "Permissions",
                "Created",
            ],
            queryset=queryset,
            row_builder=lambda role: [
                role.pk,
                role.name,
                role.description,
                role.is_system,
                len(role.permission_links.all()),
                ", ".join(sorted(link.permission.codename for link in role.permission_links.all())),
                role.created_at.isoformat(),
            ],
        )
        self.audit(
            "role.export",
            target_type="Role",
            changes={
                "rows": count,
                "format": "xlsx",
                "filters": echo_filter_params(request),
            },
        )
        return response


class PermissionViewSet(RBACPermissionMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only permission catalogue — small, fixed, unpaginated
    (SENTRA_BUILD_SPEC.md §4)."""

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    pagination_class = None

    permission_map = {
        "list": "permissions.view",
        "retrieve": "permissions.view",
    }
