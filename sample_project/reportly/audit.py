from __future__ import annotations

from typing import Any

from reportly.models import AuditEvent

_EVENTS: list[AuditEvent] = []


def reset_audit() -> None:
    _EVENTS.clear()


def emit(event: str, request_id: str, tenant_id: str, actor: str, **fields: Any) -> AuditEvent:
    record = AuditEvent(
        event=event,
        request_id=request_id,
        tenant_id=tenant_id,
        actor=actor,
        fields=dict(fields),
    )
    _EVENTS.append(record)
    return record


def trail(tenant_id: str | None = None) -> list[AuditEvent]:
    if tenant_id is None:
        return list(_EVENTS)
    return [item for item in _EVENTS if item.tenant_id == tenant_id]
