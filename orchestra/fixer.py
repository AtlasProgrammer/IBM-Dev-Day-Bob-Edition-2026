from __future__ import annotations

from orchestra.catalog import Incident

SERVICE_FIXED = '''from __future__ import annotations

from dataclasses import dataclass

from reportly.export.formatter import ReportFormatter
from reportly.models import ExportJob, ExportResult
from reportly.observability import get_logger


@dataclass
class ExportOptions:
    chunk_size: int = 65536
    atomic: bool = True


class ExportService:
    def __init__(self, formatter: ReportFormatter | None = None, options: ExportOptions | None = None) -> None:
        self.formatter = formatter or ReportFormatter()
        self.options = options or ExportOptions()
        self.log = get_logger("reportly.export")

    def export(self, job: ExportJob) -> ExportResult:
        self.log.info(
            "export.started",
            rid=job.request_id,
            report=job.report_id,
            tenant=job.tenant_id,
        )
        try:
            if job.format == "json":
                parts: list[bytes] = []
                while True:
                    chunk = job.source.read(self.options.chunk_size)
                    if not chunk:
                        break
                    parts.append(chunk)
                rendered = self.formatter.render(b"".join(parts), job.format)
                written = job.destination.write(rendered)
            else:
                written = 0
                while True:
                    chunk = job.source.read(self.options.chunk_size)
                    if not chunk:
                        break
                    written += job.destination.write(self.formatter.render_chunk(chunk, job.format))
            job.destination.flush()
            self.log.info("export.completed", rid=job.request_id, report=job.report_id, bytes=written)
            return ExportResult(ok=True, bytes_written=written, report_id=job.report_id)
        except MemoryError as exc:
            self.log.error(
                "export.failed",
                rid=job.request_id,
                report=job.report_id,
                error="MemoryError",
                detail=str(exc),
            )
            raise
        except Exception as exc:
            self.log.error(
                "export.failed",
                rid=job.request_id,
                report=job.report_id,
                error=type(exc).__name__,
                detail=str(exc),
            )
            raise
'''

OBSERVABILITY_FIXED = '''from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "x-amz-security-token"}


@dataclass
class LogRecord:
    timestamp: str
    level: str
    logger: str
    message: str
    fields: dict[str, Any]


@dataclass
class MemoryLogger:
    name: str
    records: list[LogRecord] = field(default_factory=list)

    def _emit(self, level: str, message: str, **fields: Any) -> LogRecord:
        record = LogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            logger=self.name,
            message=message,
            fields=fields,
        )
        self.records.append(record)
        return record

    def info(self, message: str, **fields: Any) -> LogRecord:
        return self._emit("INFO", message, **fields)

    def warn(self, message: str, **fields: Any) -> LogRecord:
        return self._emit("WARN", message, **fields)

    def error(self, message: str, **fields: Any) -> LogRecord:
        return self._emit("ERROR", message, **fields)


_LOGGERS: dict[str, MemoryLogger] = {}


def get_logger(name: str) -> MemoryLogger:
    if name not in _LOGGERS:
        _LOGGERS[name] = MemoryLogger(name)
    return _LOGGERS[name]


def reset_logs() -> None:
    _LOGGERS.clear()


def dump_logs() -> list[str]:
    lines: list[str] = []
    for logger in _LOGGERS.values():
        for record in logger.records:
            extras = " ".join(f"{key}={_fmt(value)}" for key, value in record.fields.items())
            lines.append(f"{record.timestamp} {record.level} {record.logger} {record.message} {extras}".rstrip())
    return lines


def _fmt(value: Any) -> str:
    text = str(value)
    if " " in text:
        return f"\\"{text}\\""
    return text


def _redact(headers: dict[str, str]) -> dict[str, str]:
    cleaned = {}
    for key, value in headers.items():
        cleaned[key.lower()] = "***" if key.lower() in SENSITIVE_HEADERS else value
    return cleaned


def log_request(request: Any) -> None:
    from reportly.config import settings

    logger = get_logger("reportly.http")
    payload: dict[str, Any] = {
        "rid": getattr(request, "request_id", ""),
        "method": getattr(request, "method", ""),
        "path": getattr(request, "path", ""),
    }
    headers = dict(getattr(request, "headers", {}) or {})
    if settings.log_request_headers:
        payload["headers"] = _redact(headers)
    logger.info("inbound", **payload)
'''

HEALTH_FIXED = '''from __future__ import annotations

from reportly.config import settings


def liveness() -> tuple[int, dict[str, object]]:
    return 200, {"status": "alive", "service": settings.service_name}


def readiness() -> tuple[int, dict[str, object]]:
    return 200, {
        "status": "ready",
        "service": settings.service_name,
        "migration": settings.migration_in_progress,
    }
'''

REGRESSION_EXPORT = '''import io
import unittest

from reportly.export.service import ExportService
from reportly.models import ExportJob


class FullReadBomb:
    def __init__(self, payload: bytes, limit: int) -> None:
        self.payload = payload
        self.limit = limit
        self.offset = 0

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            if len(self.payload) > self.limit:
                raise MemoryError("unable to allocate export buffer")
            data = self.payload[self.offset:]
            self.offset = len(self.payload)
            return data
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class TestExportRegression(unittest.TestCase):
    def test_large_export_uses_bounded_reads(self) -> None:
        payload = b"row,value\\n" * 8000
        source = FullReadBomb(payload, limit=4096)
        destination = io.BytesIO()
        job = ExportJob(
            report_id="rpt-large",
            tenant_id="acme",
            format="csv",
            source=source,
            destination=destination,
            request_id="reg-large",
        )
        result = ExportService().export(job)
        self.assertTrue(result.ok)
        self.assertEqual(destination.getvalue(), payload)

    def test_export_survives_full_read_bomb(self) -> None:
        source = FullReadBomb(b"id,name\\n1,acme\\n" * 200, limit=32)
        destination = io.BytesIO()
        job = ExportJob("rpt-bomb", "acme", "csv", source, destination, request_id="reg-bomb")
        ExportService().export(job)
        self.assertGreater(destination.tell(), 0)
'''

REGRESSION_OBS = '''import unittest

from reportly.config import settings
from reportly.models import HttpRequest
from reportly.observability import dump_logs, log_request, reset_logs


class TestObservabilityRegression(unittest.TestCase):
    def setUp(self) -> None:
        reset_logs()
        self._headers = settings.log_request_headers
        self._redact = settings.redact_secrets

    def tearDown(self) -> None:
        settings.log_request_headers = self._headers
        settings.redact_secrets = self._redact
        reset_logs()

    def test_authorization_header_is_redacted(self) -> None:
        settings.log_request_headers = True
        settings.redact_secrets = False
        log_request(
            HttpRequest(
                "POST",
                "/v1/exports",
                {"Authorization": "Bearer 0xIBM-live-secret"},
                "sec-1",
            )
        )
        text = "\\n".join(dump_logs())
        self.assertNotIn("0xIBM-live-secret", text)
        self.assertNotIn("Bearer ", text)

    def test_api_key_is_redacted(self) -> None:
        settings.log_request_headers = True
        log_request(HttpRequest("GET", "/v1/exports", {"X-Api-Key": "rk_live_reportly_21"}, "sec-2"))
        text = "\\n".join(dump_logs())
        self.assertNotIn("rk_live_reportly_21", text)
'''

AUTH_FIXED = '''from __future__ import annotations

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
    identity = REGISTRY.get(token)
    if identity is None:
        return HttpResponse(status=401, body={"error": "invalid_token"})
    claimed = request.headers.get("X-Tenant-Id") or request.headers.get("x-tenant-id")
    if claimed and claimed != identity.tenant_id:
        return HttpResponse(status=403, body={"error": "tenant_mismatch", "tenant": identity.tenant_id})
    return None
'''

REGRESSION_AUTH = '''import unittest

from reportly.api import ReportlyAPI
from reportly.audit import reset_audit
from reportly.metrics import reset_metrics
from reportly.models import HttpRequest
from reportly.quotas import reset_quotas
from reportly.webhooks import reset_webhooks


class TestTenantBindRegression(unittest.TestCase):
    def setUp(self) -> None:
        reset_audit()
        reset_metrics()
        reset_quotas()
        reset_webhooks()

    def tearDown(self) -> None:
        reset_audit()
        reset_metrics()
        reset_quotas()
        reset_webhooks()

    def test_cross_tenant_export_is_forbidden(self) -> None:
        response = ReportlyAPI().handle(
            HttpRequest(
                "POST",
                "/v1/exports",
                {
                    "Authorization": "Bearer acme-live",
                    "X-Tenant-Id": "northwind",
                    "X-Report-Id": "rpt-payroll",
                    "X-Export-Format": "csv",
                },
                "reg-x",
                b"id,name\\n1,nw\\n",
            )
        )
        self.assertEqual(response.status, 403)
        self.assertEqual(response.body["error"], "tenant_mismatch")

    def test_token_is_bound_to_tenant(self) -> None:
        response = ReportlyAPI().handle(
            HttpRequest(
                "POST",
                "/v1/exports",
                {
                    "Authorization": "Bearer acme-live",
                    "X-Tenant-Id": "acme",
                    "X-Report-Id": "rpt-acme",
                    "X-Export-Format": "csv",
                },
                "reg-ok",
                b"id,name\\n1,acme\\n",
            )
        )
        self.assertEqual(response.status, 201)
        self.assertFalse(response.body.get("cross_tenant"))
'''

REGRESSION_HEALTH = '''import unittest

from reportly.config import settings
from reportly.release.health import readiness


class TestHealthRegression(unittest.TestCase):
    def setUp(self) -> None:
        self._flag = settings.migration_in_progress

    def tearDown(self) -> None:
        settings.migration_in_progress = self._flag

    def test_readiness_stays_ready_during_migration(self) -> None:
        settings.migration_in_progress = True
        status, body = readiness()
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ready")
'''


def build_fix(incident: Incident) -> dict:
    plans = {
        "BUG-1842": {
            "title": "Restore chunked export for non-JSON streams",
            "risk": "LOW",
            "changes": [
                {
                    "file": "reportly/export/service.py",
                    "change": "Replace source.read() with a chunked loop and keep JSON minify on assembled chunks.",
                    "content": SERVICE_FIXED,
                },
                {
                    "file": "tests/test_orchestra_regression.py",
                    "change": "Add a FullReadBomb that fails unbounded reads and passes chunked reads.",
                    "content": REGRESSION_EXPORT,
                },
            ],
            "tests": ["test_large_export_uses_bounded_reads", "test_export_survives_full_read_bomb"],
        },
        "BUG-1901": {
            "title": "Redact credentials before they reach the logger",
            "risk": "LOW",
            "changes": [
                {
                    "file": "reportly/observability.py",
                    "change": "Always strip Authorization, Cookie, and API keys from inbound request logs.",
                    "content": OBSERVABILITY_FIXED,
                },
                {
                    "file": "tests/test_orchestra_regression.py",
                    "change": "Assert bearer tokens and API keys never appear in captured logs.",
                    "content": REGRESSION_OBS,
                },
            ],
            "tests": ["test_authorization_header_is_redacted", "test_api_key_is_redacted"],
        },
        "REL-2204": {
            "title": "Keep readiness on HTTP 200 during online migrations",
            "risk": "LOW",
            "changes": [
                {
                    "file": "reportly/release/health.py",
                    "change": "Readiness stays ready and exposes migration as a field instead of a 503.",
                    "content": HEALTH_FIXED,
                },
                {
                    "file": "tests/test_orchestra_regression.py",
                    "change": "Fail the build if readiness leaves 200 while a migration is running.",
                    "content": REGRESSION_HEALTH,
                },
            ],
            "tests": ["test_readiness_stays_ready_during_migration"],
        },
        "TEN-2044": {
            "title": "Bind bearer tokens to a single tenant",
            "risk": "LOW",
            "changes": [
                {
                    "file": "reportly/auth.py",
                    "change": "Reject unknown tokens and return 403 when X-Tenant-Id disagrees with the registry.",
                    "content": AUTH_FIXED,
                },
                {
                    "file": "tests/test_orchestra_regression.py",
                    "change": "Forbid acme-live from exporting Northwind and keep same-tenant exports working.",
                    "content": REGRESSION_AUTH,
                },
            ],
            "tests": ["test_cross_tenant_export_is_forbidden", "test_token_is_bound_to_tenant"],
        },
    }
    plan = plans[incident.id]
    return {
        "incident": incident.id,
        "title": plan["title"],
        "risk": plan["risk"],
        "files": len(plan["changes"]),
        "tests": plan["tests"],
        "changes": plan["changes"],
        "patch": [{"file": item["file"], "change": item["change"]} for item in plan["changes"]],
    }


def apply_changes(root, changes: list[dict]) -> None:
    for item in changes:
        target = root / item["file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8")
