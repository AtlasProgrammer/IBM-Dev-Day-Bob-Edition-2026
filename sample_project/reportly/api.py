from __future__ import annotations

from reportly.audit import emit as audit_emit
from reportly.auth import extract_bearer, require_token, resolve_identity
from reportly.config import settings
from reportly.export.service import ExportService
from reportly.flags import drift, flags
from reportly.metrics import inc, snapshot as metrics_snapshot
from reportly.models import ExportJob, HttpRequest, HttpResponse
from reportly.observability import log_request
from reportly.quotas import QuotaExceeded, consume, snapshot as quota_snapshot
from reportly.release.health import liveness, readiness
from reportly.tenants import get_tenant, list_tenants, public_tenant
from reportly.webhooks import emit as webhook_emit


class ReportlyAPI:
    def __init__(self, exporter: ExportService | None = None) -> None:
        self.exporter = exporter or ExportService()

    def handle(self, request: HttpRequest) -> HttpResponse:
        inc("http.requests")
        log_request(request)
        if request.path == "/health/live":
            status, body = liveness()
            return HttpResponse(status=status, body=body)
        if request.path == "/health/ready":
            status, body = readiness()
            return HttpResponse(status=status, body=body)
        if request.path == "/internal/drift" and request.method == "GET":
            return HttpResponse(status=200, body={"drift": drift(), "version": settings.version})
        denied = require_token(request)
        if denied:
            inc("http.denied")
            return denied
        identity = resolve_identity(request)
        claimed = request.headers.get("X-Tenant-Id") or request.headers.get("x-tenant-id")
        tenant_id = claimed or (identity.tenant_id if identity else "unknown")
        if request.path == "/v1/tenants" and request.method == "GET":
            return HttpResponse(status=200, body={"tenants": [public_tenant(item) for item in list_tenants()]})
        if request.path == "/v1/metrics" and request.method == "GET":
            return HttpResponse(status=200, body=metrics_snapshot())
        if request.path == "/v1/quota" and request.method == "GET":
            snap = quota_snapshot(tenant_id)
            return HttpResponse(
                status=200,
                body={
                    "tenant_id": snap.tenant_id,
                    "used_bytes": snap.used_bytes,
                    "monthly_bytes": snap.monthly_bytes,
                    "remaining_bytes": snap.remaining_bytes,
                },
            )
        if request.path == "/v1/exports" and request.method == "POST":
            return self._export(request, tenant_id, identity.label if identity else extract_bearer(request) or "anonymous")
        return HttpResponse(status=404, body={"error": "not_found"})

    def _export(self, request: HttpRequest, tenant_id: str, actor: str) -> HttpResponse:
        tenant = get_tenant(tenant_id)
        if tenant is None:
            return HttpResponse(status=400, body={"error": "unknown_tenant", "tenant": tenant_id})
        identity = resolve_identity(request)
        cross = bool(identity and identity.tenant_id != tenant_id)
        if flags.audit_exports:
            audit_emit(
                "export.requested",
                request.request_id,
                tenant_id,
                actor,
                cross_tenant=cross,
                token_tenant=identity.tenant_id if identity else "",
            )
        try:
            if settings.quota_enforced:
                consume(tenant_id, len(request.body))
        except QuotaExceeded as exc:
            inc("export.quota_denied")
            return HttpResponse(
                status=429,
                body={"error": "quota_exceeded", "tenant": exc.tenant_id, "limit": exc.limit},
            )
        job = ExportJob(
            report_id=request.headers.get("X-Report-Id", "unknown"),
            tenant_id=tenant_id,
            format=request.headers.get("X-Export-Format", "csv"),
            source=_BodySource(request.body),
            destination=_Buffer(),
            requested_by=actor,
            request_id=request.request_id,
        )
        try:
            result = self.exporter.export(job)
        except MemoryError:
            inc("export.oom")
            return HttpResponse(status=500, body={"error": "export_oom", "request_id": request.request_id})
        inc("export.completed")
        if flags.usage_webhooks:
            webhook_emit(
                "export.completed",
                {"tenant": tenant_id, "report_id": result.report_id, "bytes": result.bytes_written, "cross_tenant": cross},
            )
        return HttpResponse(
            status=201,
            body={
                "ok": result.ok,
                "bytes_written": result.bytes_written,
                "report_id": result.report_id,
                "tenant": tenant_id,
                "cross_tenant": cross,
            },
        )


class _BodySource:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.offset = 0

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            data = self.payload[self.offset:]
            self.offset = len(self.payload)
            return data
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class _Buffer:
    def __init__(self) -> None:
        self.chunks: list[bytes] = []

    def write(self, data: bytes) -> int:
        self.chunks.append(data)
        return len(data)

    def flush(self) -> None:
        return None
