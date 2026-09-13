from __future__ import annotations

_COUNTERS: dict[str, int] = {}
_GAUGES: dict[str, float] = {}


def reset_metrics() -> None:
    _COUNTERS.clear()
    _GAUGES.clear()


def inc(name: str, n: int = 1) -> int:
    _COUNTERS[name] = _COUNTERS.get(name, 0) + n
    return _COUNTERS[name]


def gauge(name: str, value: float) -> float:
    _GAUGES[name] = value
    return value


def snapshot() -> dict[str, object]:
    return {"counters": dict(_COUNTERS), "gauges": dict(_GAUGES)}
