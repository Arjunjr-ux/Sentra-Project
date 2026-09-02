from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from rbac.services import permission_codenames_for, roles_for

User = get_user_model()

# A real, valid hash used only as the comparison target when the email is
# unknown, so the "no such user" path still does the CPU work of a hash check.
_DUMMY_HASH = make_password("sentra-timing-equalizer")

# One message for every login failure mode — unknown email, wrong password, or
# inactive account all return this, verbatim, with a 401 (SENTRA_BUILD_SPEC.md §6).
INVALID_CREDENTIALS = "No active account found with the given credentials."


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["email", "full_name", "password"]

    def validate_email(self, value):
        value = User.objects.normalize_email(value).lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate_password(self, value):
        # Build a throwaway instance so UserAttributeSimilarityValidator has
        # something to compare against.
        candidate = User(
            email=self.initial_data.get("email", ""),
            full_name=self.initial_data.get("full_name", ""),
        )
        validate_password(value, user=candidate)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        user = User.objects.filter(email__iexact=attrs["email"].strip()).first()
        # Run a hash check even when the user is missing / inactive so the three
        # failure paths stay roughly constant-time and indistinguishable.
        if user is not None:
            password_ok = user.check_password(attrs["password"])
        else:
            check_password(attrs["password"], _DUMMY_HASH)
            password_ok = False
        if user is None or not password_ok or not user.is_active:
            raise AuthenticationFailed(INVALID_CREDENTIALS, code="authentication_failed")
        attrs["user"] = user
        return attrs


class RoleSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    is_system = serializers.BooleanField()


class MeSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_login",
            "created_at",
            "updated_at",
            "roles",
            "permissions",
        ]
        read_only_fields = fields

    @staticmethod
    def get_roles(obj) -> list[dict]:
        return RoleSummarySerializer(roles_for(obj), many=True).data

    @staticmethod
    def get_permissions(obj) -> list[str]:
        return permission_codenames_for(obj)
