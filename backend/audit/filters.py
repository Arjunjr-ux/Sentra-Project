from django_filters import rest_framework as filters

from .models import AuditLog


class AuditLogFilter(filters.FilterSet):
    """`?actor=<id>`, `?action=`, `?date_from=`, `?date_to=` for the audit-log
    list (SENTRA_BUILD_SPEC.md §4). Dates are inclusive on ``created_at``."""

    actor = filters.UUIDFilter(field_name="actor_id")
    action = filters.CharFilter(field_name="action", lookup_expr="iexact")
    date_from = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = AuditLog
        fields = ["actor", "action", "date_from", "date_to"]
