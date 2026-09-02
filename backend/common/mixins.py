from audit.services import write_audit

from .utils import get_client_ip


class AuditMixin:
    """Give a viewset a terse ``self.audit(action, target=..., changes=...)``
    that stamps the actor and client IP automatically."""

    def audit(self, action, *, target=None, target_type="", target_id="", changes=None):
        request = self.request
        return write_audit(
            actor=request.user if request.user.is_authenticated else None,
            action=action,
            target=target,
            target_type=target_type,
            target_id=target_id,
            changes=changes or {},
            ip=get_client_ip(request),
        )
