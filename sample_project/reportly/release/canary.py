from __future__ import annotations

from dataclasses import dataclass, field

from reportly.release.health import readiness


@dataclass
class CanaryState:
    revision: str
    share: int = 10
    probes: list[dict[str, object]] = field(default_factory=list)
    rolled_back: bool = False
    reason: str = ""


def evaluate_probe(state: CanaryState) -> CanaryState:
    status, body = readiness()
    state.probes.append({"status": status, "body": body})
    if status != 200:
        state.rolled_back = True
        state.share = 0
        state.reason = "readiness_failed"
    return state
