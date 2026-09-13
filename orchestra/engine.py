from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from orchestra.agents import (
    PARALLEL_INVESTIGATORS,
    code_reviewer,
    document_analyst,
    release_officer,
)
from orchestra.catalog import get_incident
from orchestra.fixer import build_fix
from orchestra.impact import estimate
from orchestra.validator import validate_incident


Emit = Callable[[str, dict], None]


def _emit(emit: Emit | None, event: str, data: dict) -> None:
    if emit:
        emit(event, data)


def investigate(incident_id: str, emit: Emit | None = None) -> dict:
    incident = get_incident(incident_id)
    started = time.perf_counter()
    _emit(emit, "phase", {"phase": "understand", "incident": incident.id})
    documents = document_analyst(incident)
    _emit(emit, "agent", documents)
    _emit(emit, "phase", {"phase": "investigate", "incident": incident.id})
    agents = [documents]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fn, incident): fn for fn in PARALLEL_INVESTIGATORS}
        for future in as_completed(futures):
            result = future.result()
            agents.append(result)
            _emit(emit, "agent", result)
    order = {
        "Document Analyst": 0,
        "Code Investigator": 1,
        "Log Analyst": 2,
        "Git Historian": 3,
        "Test Engineer": 4,
    }
    agents.sort(key=lambda item: order[item["agent"]])
    root = synthesize(incident, agents)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    impact = estimate(incident, elapsed_ms)
    payload = {
        "incident": incident.public(),
        "agents": agents,
        "root_cause": root,
        "elapsed_ms": elapsed_ms,
        "manual_minutes": impact["manual_minutes"],
        "orchestra_minutes": impact["orchestra_minutes"],
        "impact": impact,
        "bob": {
            "agent_mode": "agents/orchestrator.md",
            "parallel": [item["skill"] for item in agents if item["id"] != "document-analyst"],
            "documents": [item for item in incident.focus if item.endswith(".md")],
        },
    }
    _emit(emit, "synthesis", root)
    _emit(emit, "complete", payload)
    return payload


def synthesize(incident, agents: list[dict]) -> dict:
    titles = {
        "BUG-1842": "ExportService loads the complete report into memory",
        "BUG-1901": "Request logging persists live bearer tokens",
        "REL-2204": "Readiness 503 during online migration drains the canary",
        "TEN-2044": "require_token never binds a bearer to a tenant",
    }
    explanations = {
        "BUG-1842": "Documents require bounded memory, the code still calls source.read(), production logs show MemoryError on a 734 MB report, git points at commit 81f92a, and tests never exercise a large stream.",
        "BUG-1901": "Architecture forbids secrets in logs, observability forwards Authorization when redaction is off, access logs already contain a live token, and no test asserts redaction.",
        "REL-2204": "The release contract keeps /health/ready on HTTP 200 during online migrations, health.py returns 503 instead, the canary log records the rollback, and tests only cover the idle path.",
        "TEN-2044": "Security and onboarding require a 403 on tenant mismatch, auth accepts any non-expired bearer, the API trusts X-Tenant-Id, audit already recorded Acme exporting Northwind payroll, and no test forbids the path.",
    }
    evidence = []
    for agent in agents:
        evidence.extend(agent.get("evidence") or [])
    agreeing = sum(1 for agent in agents if agent.get("findings"))
    confidence = min(0.97, 0.58 + 0.08 * agreeing)
    return {
        "title": titles[incident.id],
        "confidence": confidence,
        "explanation": explanations[incident.id],
        "evidence": evidence,
        "agreeing_agents": agreeing,
    }


def plan_fix(incident_id: str) -> dict:
    return build_fix(get_incident(incident_id))


def run_validation(incident_id: str, emit: Emit | None = None) -> dict:
    incident = get_incident(incident_id)
    _emit(emit, "phase", {"phase": "verify", "incident": incident.id})
    tests = validate_incident(incident)
    _emit(emit, "tests", tests)
    patch = build_fix(incident)
    review = code_reviewer(incident, patch, tests)
    release = release_officer(incident, tests, review)
    _emit(emit, "agent", review)
    _emit(emit, "agent", release)
    impact = estimate(incident)
    payload = {
        "incident": incident.public(),
        "tests": tests,
        "review": review.get("review", {}),
        "readiness": release.get("readiness", 0),
        "decision": release.get("decision", "HOLD MERGE"),
        "manual_minutes": impact["manual_minutes"],
        "orchestra_minutes": impact["orchestra_minutes"],
        "saved_minutes": impact["saved_minutes"],
        "reduction_pct": impact["reduction_pct"],
        "impact": impact,
        "agents": [review, release],
    }
    _emit(emit, "complete", payload)
    return payload
