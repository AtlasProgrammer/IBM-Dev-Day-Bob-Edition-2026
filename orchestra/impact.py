from __future__ import annotations

from orchestra.catalog import Incident


def estimate(incident: Incident, elapsed_ms: int = 0) -> dict:
    orchestra_minutes = max(6, round(incident.manual_minutes * 0.08))
    saved = incident.manual_minutes - orchestra_minutes
    reduction = round(100 * saved / incident.manual_minutes)
    return {
        "manual_minutes": incident.manual_minutes,
        "orchestra_minutes": orchestra_minutes,
        "saved_minutes": saved,
        "reduction_pct": reduction,
        "elapsed_ms": elapsed_ms,
        "manual_steps": [
            "Read ticket, ADRs, runbooks, and architecture",
            "Search logs and correlate request ids",
            "Walk git blame and isolate the regression window",
            "Inspect tests for a missing guard",
            "Hand-write a fix and a regression test",
            "Re-run the suite and wait on review",
        ],
        "orchestra_steps": [
            "Document analyst extracts MUST invariants",
            "Four investigators run in parallel",
            "Root cause is synthesized with citations",
            "Patch and regression tests are applied in an isolated tree",
            "Review axes and release gate score the merge",
        ],
    }
