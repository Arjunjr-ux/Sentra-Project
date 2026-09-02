from django_filters import rest_framework as filters

from .models import Role


class RoleFilter(filters.FilterSet):
    is_system = filters.BooleanFilter()

    class Meta:
        model = Role
        fields = ["is_system"]
