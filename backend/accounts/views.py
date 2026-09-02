from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from audit.services import write_audit
from common.throttling import AuthRateThrottle
from common.utils import get_client_ip
from rbac.models import Role
from rbac.services import assign_role

from .cookies import clear_refresh_cookie, set_refresh_cookie
from .serializers import LoginSerializer, MeSerializer, RegisterSerializer

User = get_user_model()

DEFAULT_SIGNUP_ROLE = "Viewer"

_access_response = inline_serializer(
    name="AccessTokenResponse", fields={"access": serializers.CharField()}
)


def _issue_tokens(user, response):
    """Mint an access + refresh pair, attach the refresh cookie, return access."""
    refresh = RefreshToken.for_user(user)
    set_refresh_cookie(response, refresh)
    return str(refresh.access_token)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    serializer_class = RegisterSerializer

    @extend_schema(request=RegisterSerializer, responses={201: _access_response})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        viewer_role = Role.objects.filter(name=DEFAULT_SIGNUP_ROLE).first()
        if viewer_role is not None:
            assign_role(user, viewer_role, assigned_by=None)

        response = Response(status=status.HTTP_201_CREATED)
        response.data = {"access": _issue_tokens(user, response)}
        write_audit(
            actor=user,
            action="auth.register",
            target=user,
            changes={"email": user.email},
            ip=get_client_ip(request),
        )
        return response


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]
    serializer_class = LoginSerializer

    @extend_schema(request=LoginSerializer, responses={200: _access_response})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        response = Response(status=status.HTTP_200_OK)
        response.data = {"access": _issue_tokens(user, response)}
        write_audit(
            actor=user,
            action="auth.login",
            target=user,
            ip=get_client_ip(request),
        )
        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={200: _access_response})
    def post(self, request):
        raw = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if not raw:
            return _unauthorized()

        try:
            # Parsing verifies signature, expiry, and blacklist status. A reused
            # (already-rotated) token is blacklisted and raises here.
            old = RefreshToken(raw)
        except TokenError:
            return _unauthorized()

        try:
            old.blacklist()
        except AttributeError:
            pass

        user = User.objects.filter(id=old.get("user_id"), is_active=True).first()
        if user is None:
            return _unauthorized()

        response = Response(status=status.HTTP_200_OK)
        response.data = {"access": _issue_tokens(user, response)}
        write_audit(actor=user, action="auth.refresh", ip=get_client_ip(request))
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: OpenApiResponse(description="No Content")})
    def post(self, request):
        raw = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        actor = request.user if request.user.is_authenticated else None
        if raw:
            try:
                token = RefreshToken(raw)
                if actor is None:
                    actor = User.objects.filter(id=token.get("user_id")).first()
                token.blacklist()
            except (TokenError, AttributeError):
                pass

        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        if actor is not None:
            write_audit(actor=actor, action="auth.logout", ip=get_client_ip(request))
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    @extend_schema(responses={200: MeSerializer})
    def get(self, request):
        return Response(MeSerializer(request.user).data)


def _unauthorized():
    return Response(
        {"detail": "Invalid or expired refresh token."},
        status=status.HTTP_401_UNAUTHORIZED,
    )
