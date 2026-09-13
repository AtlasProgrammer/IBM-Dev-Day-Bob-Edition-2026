from __future__ import annotations

from reportly.models import HttpRequest, HttpResponse, Identity

REGISTRY: dict[str, Identity] = {
    "demo-token": Identity("demo-token", "demo", ("export",), "Demo CLI"),
    "acme-live": Identity("acme-live", "acme", ("export",), "Acme batch"),
    "northwind-live": Identity("northwind-live", "northwind", ("export",), "Northwind batch"),
    "platform-ops": Identity("platform-ops", "platform", ("export", "admin"), "Platform ops"),
}


def extract_bearer(request: HttpRequest) -> str | None:
    header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not header:
        return None
    prefix = "Bearer "
    if header.startswith(prefix):
        return header[len(prefix):]
    return header


def resolve_identity(request: HttpRequest) -> Identity | None:
    token = extract_bearer(request)
    if not token:
        return None
    return REGISTRY.get(token)


def require_token(request: HttpRequest) -> HttpResponse | None:
    token = extract_bearer(request)
    if not token:
        return HttpResponse(status=401, body={"error": "missing_token"})
    if token.startswith("expired-"):
        return HttpResponse(status=401, body={"error": "expired_token"})
    return None
