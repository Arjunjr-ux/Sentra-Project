from rest_framework.throttling import SimpleRateThrottle


class AuthRateThrottle(SimpleRateThrottle):
    """Dedicated 5/min-per-IP throttle for register/ and login/.

    Always keys on the client IP (never the user), so it is a true per-IP limit
    and is independent of the general ``anon`` rate (SENTRA_BUILD_SPEC.md §6).
    """

    scope = "auth"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
