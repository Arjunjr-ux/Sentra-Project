import json

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import filters, viewsets
from rest_framework.decorators import action

from common.exports import build_xlsx_response
from common.mixins import AuditMixin
from common.utils import echo_filter_params
from rbac.permissions import RBACPermissionMixin

from .filters import AuditLogFilter
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(RBACPermissionMixin, AuditMixin, viewsets.ReadOnlyModelViewSet):
    """Append-only audit trail, read-only via the API (SENTRA_BUILD_SPEC.md §4)."""

    queryset = AuditLog.objects.select_related("actor").all()
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ["action", "actor__email", "target_type", "target_id"]
    ordering_fields = ["created_at", "action"]
    ordering = ["-created_at"]

    permission_map = {
        "list": "audit.view",
        "retrieve": "audit.view",
        "export": "audit.view",
    }

    @extend_schema(responses={200: OpenApiResponse(description="An .xlsx file")})
    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        response, count = build_xlsx_response(
            filename="audit-logs.xlsx",
            headers=[
                "ID",
                "Timestamp",
                "Actor",
                "Action",
                "Target type",
                "Target id",
                "IP",
                "Changes",
            ],
            queryset=queryset,
            row_builder=lambda entry: [
                entry.pk,
                entry.created_at.isoformat(),
                entry.actor.email if entry.actor_id else "",
                entry.action,
                entry.target_type,
                entry.target_id,
                entry.ip or "",
                json.dumps(entry.changes, default=str),
            ],
        )
        self.audit(
            "audit.export",
            target_type="AuditLog",
            changes={
                "rows": count,
                "format": "xlsx",
                "filters": echo_filter_params(request),
            },
        )
        return response
