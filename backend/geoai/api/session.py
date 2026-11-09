"""Exact session boundary. Never log request headers, targets or credentials."""
from dataclasses import dataclass, field
import hmac
import logging
import secrets

from starlette.responses import JSONResponse, Response

PRODUCTION_ORIGINS = ("tauri://localhost", "http://tauri.localhost")
DEVELOPMENT_ORIGINS = ("http://127.0.0.1:1420",)


@dataclass(frozen=True, repr=False)
class SessionPolicy:
    port: int
    token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    allowed_origins: tuple[str, ...] = PRODUCTION_ORIGINS
    allow_missing_origin: bool = False

    def __post_init__(self):
        if not 1 <= self.port <= 65535 or not self.token or not self.token.isascii():
            raise ValueError("Invalid session configuration")
        if not self.allowed_origins or any(o not in PRODUCTION_ORIGINS + DEVELOPMENT_ORIGINS for o in self.allowed_origins):
            raise ValueError("Unsupported origin configuration")


class SanitizedLogFilter(logging.Filter):
    """Drop raw messages and exception text, including request URLs, at sink."""
    def filter(self, record):
        record.msg = "GeoAI runtime diagnostic (details withheld)"
        record.args = ()
        record.exc_info = record.exc_text = record.stack_info = None
        return True


class SessionBoundary:
    def __init__(self, app, policy: SessionPolicy):
        self.app, self.policy = app, policy

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        values = {}
        duplicate = False
        for name, value in scope["headers"]:
            name = name.lower()
            if name in (b"host", b"origin", b"authorization", b"access-control-request-method", b"access-control-request-headers"):
                duplicate |= name in values
                values[name] = value
        policy = self.policy
        origin = values.get(b"origin")
        origin_ok = origin in [o.encode("ascii") for o in policy.allowed_origins]
        host_ok = values.get(b"host") == f"127.0.0.1:{policy.port}".encode("ascii")
        if duplicate or not host_ok:
            response = JSONResponse({"detail": "Session request rejected"}, status_code=403)
        elif scope["method"] == "OPTIONS":
            # Browser preflight grants only CORS metadata, never route authorization.
            requested = {v.strip().lower() for v in values.get(b"access-control-request-headers", b"").split(b",") if v.strip()}
            if (not origin_ok or values.get(b"access-control-request-method") != b"GET"
                    or requested != {b"authorization"} or scope["path"] not in ("/v1/health", "/v1/capabilities") or scope.get("query_string")):
                response = JSONResponse({"detail": "Session request rejected"}, status_code=403)
            else:
                response = Response(status_code=204, headers={"Access-Control-Allow-Origin": origin.decode("ascii"), "Access-Control-Allow-Methods": "GET", "Access-Control-Allow-Headers": "Authorization", "Vary": "Origin"})
        elif not hmac.compare_digest(values.get(b"authorization", b""), b"Bearer " + policy.token.encode("ascii")):
            response = JSONResponse({"detail": "Session authorization required"}, status_code=401)
        elif (origin is not None and not origin_ok) or (origin is None and not policy.allow_missing_origin) or scope.get("query_string"):
            response = JSONResponse({"detail": "Session request rejected"}, status_code=403)
        else:
            async def cors_send(message):
                if message["type"] == "http.response.start" and origin_ok:
                    message["headers"] = list(message["headers"]) + [(b"access-control-allow-origin", origin), (b"vary", b"Origin")]
                await send(message)
            return await self.app(scope, receive, cors_send)
        await response(scope, receive, send)
