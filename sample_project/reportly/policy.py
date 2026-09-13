from __future__ import annotations

from reportly.flags import drift


def evaluate(tests_failed: int, review: dict[str, str] | None = None) -> dict[str, object]:
    axes = review or {}
    gates = {
        "tests": tests_failed == 0,
        "review": all(value == "PASS" for value in axes.values()) if axes else True,
        "invariants": len(drift()) == 0,
    }
    return {
        "allow_merge": all(gates.values()),
        "gates": gates,
        "drift": drift(),
    }
