from __future__ import annotations

from reportly.models import QuotaSnapshot
from reportly.tenants import get_tenant


class QuotaExceeded(Exception):
    def __init__(self, tenant_id: str, used: int, limit: int) -> None:
        super().__init__(f"quota exceeded for {tenant_id}")
        self.tenant_id = tenant_id
        self.used = used
        self.limit = limit


_USED: dict[str, int] = {}


def reset_quotas() -> None:
    _USED.clear()


def snapshot(tenant_id: str) -> QuotaSnapshot:
    tenant = get_tenant(tenant_id)
    limit = tenant.monthly_bytes if tenant else 0
    return QuotaSnapshot(tenant_id=tenant_id, used_bytes=_USED.get(tenant_id, 0), monthly_bytes=limit)


def consume(tenant_id: str, nbytes: int) -> QuotaSnapshot:
    current = snapshot(tenant_id)
    if current.monthly_bytes <= 0:
        return current
    nxt = current.used_bytes + max(0, nbytes)
    if nxt > current.monthly_bytes:
        raise QuotaExceeded(tenant_id, current.used_bytes, current.monthly_bytes)
    _USED[tenant_id] = nxt
    return snapshot(tenant_id)
