from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_email",
            "action",
            "target_type",
            "target_id",
            "changes",
            "ip",
            "created_at",
        ]
        read_only_fields = fields

    @extend_schema_field({"type": "string", "nullable": True})
    def get_actor_email(self, obj) -> str | None:
        return obj.actor.email if obj.actor_id else None
