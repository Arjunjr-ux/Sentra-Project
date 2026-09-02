from django.contrib.auth import get_user_model
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.response import Response

from common.exports import build_xlsx_response
from common.mixins import AuditMixin
from common.utils import echo_filter_params
from rbac.models import Role, UserRole
from rbac.permissions import RBACPermissionMixin
from rbac.serializers import UserRolesReplaceSerializer

from .filters import UserFilter
from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
    _prefetched_roles,
)

User = get_user_model()

_USER_PREFETCH = "role_links__role__permission_links__permission"
ADMIN_ROLE_NAME = "Admin"


class UserViewSet(RBACPermissionMixin, AuditMixin, viewsets.ModelViewSet):
    """User CRUD. DELETE is a soft-deactivate — a user row is never destroyed
    (SENTRA_BUILD_SPEC.md §4)."""

    queryset = User.objects.all().prefetch_related(_USER_PREFETCH)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter
    search_fields = ["email", "full_name"]
    ordering_fields = ["email", "full_name", "created_at", "last_login", "is_active"]
    ordering = ["-created_at"]

    permission_map = {
        "list": "users.view",
        "retrieve": "users.view",
        "create": "users.create",
        "update": "users.edit",
        "partial_update": "users.edit",
        "destroy": "users.delete",
        "replace_roles": "roles.manage",
        "export": "users.view",
    }

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in {"update", "partial_update"}:
            return UserUpdateSerializer
        if self.action == "replace_roles":
            return UserRolesReplaceSerializer
        return UserSerializer

    # --- create / update / soft-delete --------------------------------------

    def perform_create(self, serializer):
        user = serializer.save()
        self.audit(
            "user.create",
            target=user,
            changes={"email": user.email, "full_name": user.full_name},
        )

    @extend_schema(exclude=True)
    def update(self, request, *args, **kwargs):
        # §4 exposes GET/PATCH/DELETE on /users/{id}/ — full-replace PUT is not
        # part of the contract.
        if not kwargs.get("partial", False):
            raise MethodNotAllowed(request.method)
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance
        if (
            instance.pk == self.request.user.pk
            and serializer.validated_data.get("is_active") is False
        ):
            raise ValidationError("You cannot deactivate your own account.")

        tracked = ["full_name", "email", "is_active"]
        before = {field: getattr(instance, field) for field in tracked}
        user = serializer.save()
        changes = {
            field: [before[field], getattr(user, field)]
            for field in tracked
            if before[field] != getattr(user, field)
        }
        self.audit("user.update", target=user, changes=changes)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            raise ValidationError("You cannot deactivate your own account.")
        if user.is_active:
            user.is_active = False
            user.save(update_fields=["is_active", "updated_at"])
        self.audit("user.deactivate", target=user, changes={"is_active": [True, False]})
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- PUT /users/{id}/roles/ -------------------------------------------

    @extend_schema(request=UserRolesReplaceSerializer, responses={200: UserSerializer})
    @action(detail=True, methods=["put"], url_path="roles")
    def replace_roles(self, request, pk=None):
        user = self.get_object()
        serializer = UserRolesReplaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_roles = serializer.validated_data["role_ids"]
        new_ids = {role.pk for role in new_roles}
        old_ids = set(UserRole.objects.filter(user=user).values_list("role_id", flat=True))

        self._guard_last_admin(request, user, old_ids, new_ids)

        with transaction.atomic():
            UserRole.objects.filter(user=user, role_id__in=old_ids - new_ids).delete()
            UserRole.objects.bulk_create(
                UserRole(user=user, role=role, assigned_by=request.user)
                for role in new_roles
                if role.pk not in old_ids
            )

        self.audit(
            "user.roles.replace",
            target=user,
            changes={"roles": [sorted(old_ids), sorted(new_ids)]},
        )
        fresh = self.get_queryset().get(pk=user.pk)
        return Response(UserSerializer(fresh).data)

    @staticmethod
    def _guard_last_admin(request, user, old_ids, new_ids):
        if user.pk != request.user.pk:
            return
        admin_role = Role.objects.filter(name=ADMIN_ROLE_NAME).first()
        if admin_role is None:
            return
        removing_admin = admin_role.pk in old_ids and admin_role.pk not in new_ids
        if not removing_admin:
            return
        others_hold_admin = UserRole.objects.filter(role=admin_role).exclude(user=user).exists()
        if not others_hold_admin:
            raise ValidationError("You cannot remove your own last Admin role assignment.")

    # --- GET /users/export/ --------------------------------------------

    @extend_schema(responses={200: OpenApiResponse(description="An .xlsx file")})
    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        response, count = build_xlsx_response(
            filename="users.xlsx",
            headers=[
                "ID",
                "Email",
                "Full name",
                "Active",
                "Staff",
                "Roles",
                "Last login",
                "Created",
            ],
            queryset=queryset,
            row_builder=lambda user: [
                str(user.id),
                user.email,
                user.full_name,
                user.is_active,
                user.is_staff,
                ", ".join(role.name for role in _prefetched_roles(user)),
                user.last_login.isoformat() if user.last_login else "",
                user.created_at.isoformat(),
            ],
        )
        self.audit(
            "user.export",
            target_type="User",
            changes={
                "rows": count,
                "format": "xlsx",
                "filters": echo_filter_params(request),
            },
        )
        return response
