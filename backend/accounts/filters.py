from django_filters import rest_framework as filters

from .models import User


class UserFilter(filters.FilterSet):
    """`?role=<id>` and `?is_active=` field filters for the users list
    (SENTRA_BUILD_SPEC.md §4)."""

    role = filters.NumberFilter(field_name="role_links__role_id", distinct=True)
    is_active = filters.BooleanFilter()

    class Meta:
        model = User
        fields = ["role", "is_active"]
