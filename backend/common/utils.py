def get_client_ip(request) -> str | None:
    """Best-effort client IP.

    Honours the first hop in ``X-Forwarded-For`` (Render / any reverse proxy sits
    in front of the app), falling back to ``REMOTE_ADDR``.
    """

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None
