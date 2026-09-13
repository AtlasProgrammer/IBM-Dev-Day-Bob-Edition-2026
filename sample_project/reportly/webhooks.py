from __future__ import annotations

from typing import Any

_QUEUE: list[dict[str, Any]] = []


def reset_webhooks() -> None:
    _QUEUE.clear()


def emit(topic: str, payload: dict[str, Any]) -> dict[str, Any]:
    item = {"topic": topic, "payload": payload, "attempts": 1, "status": "delivered"}
    _QUEUE.append(item)
    return item


def pending() -> list[dict[str, Any]]:
    return list(_QUEUE)
