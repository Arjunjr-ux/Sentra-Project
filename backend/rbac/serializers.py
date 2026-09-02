from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Permission, Role


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "description"]
        read_only_fields = fields


class RoleSerializer(serializers.ModelSerializer):
    """Read representation: includes the flattened permission codenames and a
    count for the role-list UI."""

    permissions = serializers.SerializerMethodField()
    permission_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "is_system",
            "created_at",
            "permissions",
            "permission_count",
        ]
        read_only_fields = fields

    @extend_schema_field({"type": "array", "items": {"type": "string"}})
    def get_permissions(self, obj) -> list:
        return sorted(link.permission.codename for link in obj.permission_links.all())

    @extend_schema_field({"type": "integer"})
    def get_permission_count(self, obj) -> int:
        return len(obj.permission_links.all())


class RoleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        qs = Role.objects.filter(name__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A role with that name already exists.")
        return value


class RolePermissionsReplaceSerializer(serializers.Serializer):
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        error_messages={
            "does_not_exist": 'Permission with id "{pk_value}" does not exist.',
            "incorrect_type": "Permission ids must be integers.",
        },
    )


class UserRolesReplaceSerializer(serializers.Serializer):
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        error_messages={
            "does_not_exist": 'Role with id "{pk_value}" does not exist.',
            "incorrect_type": "Role ids must be integers.",
        },
    )
