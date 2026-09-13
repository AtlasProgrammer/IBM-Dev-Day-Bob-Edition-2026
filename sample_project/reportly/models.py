from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class Readable(Protocol):
    def read(self, size: int = -1) -> bytes:
        ...


class Writable(Protocol):
    def write(self, data: bytes) -> int:
        ...

    def flush(self) -> None:
        ...


@dataclass(frozen=True)
class Identity:
    token: str
    tenant_id: str
    scopes: tuple[str, ...]
    label: str = ""


@dataclass(frozen=True)
class Tenant:
    id: str
    name: str
    plan: str
    monthly_bytes: int
    region: str


@dataclass
class QuotaSnapshot:
    tenant_id: str
    used_bytes: int
    monthly_bytes: int

    @property
    def remaining_bytes(self) -> int:
        return max(0, self.monthly_bytes - self.used_bytes)


@dataclass
class AuditEvent:
    event: str
    request_id: str
    tenant_id: str
    actor: str
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExportJob:
    report_id: str
    tenant_id: str
    format: str
    source: Any
    destination: Any
    requested_by: str = "system"
    request_id: str = ""


@dataclass
class ExportResult:
    ok: bool
    bytes_written: int
    report_id: str
    error: str | None = None


@dataclass
class HttpRequest:
    method: str
    path: str
    headers: dict[str, str]
    request_id: str
    body: bytes = b""


@dataclass
class HttpResponse:
    status: int
    body: dict[str, Any]
    headers: dict[str, str] | None = None
