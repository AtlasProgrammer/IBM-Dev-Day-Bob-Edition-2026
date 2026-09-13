from __future__ import annotations

from reportly.config import settings


def liveness() -> tuple[int, dict[str, object]]:
    return 200, {"status": "alive", "service": settings.service_name}


def readiness() -> tuple[int, dict[str, object]]:
    if settings.migration_in_progress:
        return settings.canary_ready_status, {
            "status": "migrating",
            "service": settings.service_name,
        }
    return 200, {"status": "ready", "service": settings.service_name}
