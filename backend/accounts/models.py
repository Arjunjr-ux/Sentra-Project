import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser):
    """Custom user: UUID pk, email login, no username (SENTRA_BUILD_SPEC.md §3).

    Deliberately does *not* use ``PermissionsMixin`` — that would attach M2M
    relations to ``auth.Group`` / ``auth.Permission``, and §3 requires the RBAC
    vocabulary to be owned entirely by the ``rbac`` app. ``is_superuser`` is kept
    as a plain flag so Django's admin login still works for superusers.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["-created_at"]
        # `email` is already indexed via unique=True (SENTRA_BUILD_SPEC.md §3).

    def __str__(self):
        return self.email

    # --- minimal permission surface (superuser-only; real RBAC lives in `rbac`) --

    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_superuser

    def has_perms(self, perm_list, obj=None):
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        return self.is_active and self.is_superuser
