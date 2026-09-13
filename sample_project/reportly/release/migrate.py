from __future__ import annotations

from reportly.config import settings
from reportly.observability import get_logger


def begin_online_migration() -> None:
    settings.migration_in_progress = True
    get_logger("reportly.release").info("migration.started", mode="online")


def finish_online_migration() -> None:
    settings.migration_in_progress = False
    get_logger("reportly.release").info("migration.finished", mode="online")
