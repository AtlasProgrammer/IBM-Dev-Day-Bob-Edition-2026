from __future__ import annotations

from reportly.models import Tenant

CATALOG: dict[str, Tenant] = {
    "acme": Tenant("acme", "Acme Analytics", "enterprise", 50_000_000_000, "us-east"),
    "northwind": Tenant("northwind", "Northwind Trading", "business", 8_000_000_000, "eu-central"),
    "demo": Tenant("demo", "Reportly Demo", "trial", 50_000_000, "us-east"),
    "platform": Tenant("platform", "Reportly Platform", "internal", 10_000_000_000, "us-east"),
}


def get_tenant(tenant_id: str) -> Tenant | None:
    return CATALOG.get(tenant_id)


def list_tenants() -> list[Tenant]:
    return list(CATALOG.values())


def public_tenant(tenant: Tenant) -> dict[str, object]:
    return {
        "id": tenant.id,
        "name": tenant.name,
        "plan": tenant.plan,
        "monthly_bytes": tenant.monthly_bytes,
        "region": tenant.region,
    }
