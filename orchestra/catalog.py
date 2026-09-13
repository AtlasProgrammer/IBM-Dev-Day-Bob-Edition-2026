from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from orchestra.paths import AGENTS, SAMPLE


@dataclass(frozen=True)
class Incident:
    id: str
    severity: str
    workflow: str
    title: str
    summary: str
    tenant: str
    request_id: str
    focus: list[str]
    signals: list[str]
    manual_minutes: int
    bob_features: list[str] = field(default_factory=list)

    def public(self) -> dict:
        return {
            "id": self.id,
            "severity": self.severity,
            "workflow": self.workflow,
            "title": self.title,
            "summary": self.summary,
            "tenant": self.tenant,
            "request_id": self.request_id,
            "focus": self.focus,
            "signals": self.signals,
            "manual_minutes": self.manual_minutes,
            "bob_features": self.bob_features,
            "ticket": _read(SAMPLE / "incidents" / f"{self.id}.md"),
        }


INCIDENTS = {
    "BUG-1842": Incident(
        id="BUG-1842",
        severity="SEV-2",
        workflow="Debugging + Testing",
        title="Large report export returns HTTP 500",
        summary="A 734 MB monthly export dies with MemoryError after ExportService buffers the entire report.",
        tenant="acme",
        request_id="req-7f3a",
        focus=[
            "reportly/export/service.py",
            "reportly/export/streaming.py",
            "reportly/flags.py",
            "logs/application.log",
            "docs/adr/0003-in-memory-export-buffer.md",
            "docs/runbooks/export-oom.md",
            "tests/test_export.py",
        ],
        signals=["MemoryError", "source.read()", "bounded memory", "81f92a"],
        manual_minutes=95,
        bob_features=["Agent Mode", "Parallel tasks", "Document understanding"],
    ),
    "BUG-1901": Incident(
        id="BUG-1901",
        severity="SEV-1",
        workflow="Code review + Security",
        title="Bearer tokens written to application logs",
        summary="Production access logs persist Authorization headers and API keys because redaction is disabled.",
        tenant="northwind",
        request_id="req-aa19",
        focus=[
            "reportly/observability.py",
            "reportly/config.py",
            "reportly/flags.py",
            "logs/access.log",
            "docs/adr/0005-request-logging.md",
            "docs/architecture.md",
            "tests/test_observability.py",
        ],
        signals=["Authorization", "Bearer", "redact_secrets", "c3e118"],
        manual_minutes=80,
        bob_features=["Agent Mode", "Document understanding", "Subagents"],
    ),
    "REL-2204": Incident(
        id="REL-2204",
        severity="SEV-2",
        workflow="Release + Deployment",
        title="Canary deploy rolled back during online migration",
        summary="Readiness returns 503 while a migration runs, so the canary is drained and the pipeline rolls back.",
        tenant="platform",
        request_id="rel-2204",
        focus=[
            "reportly/release/health.py",
            "reportly/release/migrate.py",
            "reportly/release/canary.py",
            "logs/deploy-canary.log",
            "docs/runbooks/canary-rollback.md",
            "docs/architecture.md",
            "tests/test_health.py",
        ],
        signals=["503", "readiness", "migration_in_progress", "e71bb2"],
        manual_minutes=70,
        bob_features=["Agent Mode", "Parallel tasks", "Document understanding"],
    ),
    "TEN-2044": Incident(
        id="TEN-2044",
        severity="SEV-1",
        workflow="Maintenance + Security",
        title="Cross-tenant export accepted",
        summary="Acme bearer acme-live exports Northwind payroll because require_token never binds the token to a tenant.",
        tenant="northwind",
        request_id="req-t2044",
        focus=[
            "reportly/auth.py",
            "reportly/api.py",
            "reportly/flags.py",
            "logs/tenant-isolation.log",
            "docs/adr/0007-trust-tenant-header.md",
            "docs/security.md",
            "docs/onboarding.md",
            "tests/test_auth.py",
        ],
        signals=["X-Tenant-Id", "cross_tenant", "tenant.assumed", "a91c03"],
        manual_minutes=85,
        bob_features=["Agent Mode", "Document understanding", "Subagents", "Parallel tasks"],
    ),
}


CAPABILITIES = [
    {
        "feature": "Agent Mode",
        "skill": "agents/orchestrator.md",
        "use": "Owns the incident-to-merge workflow and refuses a merge without evidence.",
    },
    {
        "feature": "Parallel tasks / subagents",
        "skill": "agents/code-investigator.md",
        "use": "Code, logs, git, and tests investigate the same incident at the same time.",
    },
    {
        "feature": "Document understanding",
        "skill": "agents/document-analyst.md",
        "use": "Architecture, ADRs, runbooks, security, and onboarding are treated as evidence.",
    },
    {
        "feature": "Verification loop",
        "skill": "agents/test-engineer.md",
        "use": "The proposed fix is patched, tested, reviewed, and scored for release readiness.",
    },
]


def get_incident(incident_id: str) -> Incident:
    if incident_id not in INCIDENTS:
        raise KeyError(incident_id)
    return INCIDENTS[incident_id]


def list_incidents() -> list[dict]:
    return [item.public() for item in INCIDENTS.values()]


def list_skills() -> list[dict]:
    items = []
    for path in sorted(AGENTS.glob("*.md")):
        items.append(
            {
                "id": path.stem,
                "path": f"agents/{path.name}",
                "title": path.stem.replace("-", " ").title(),
                "body": path.read_text(encoding="utf-8"),
            }
        )
    return items


def project_index() -> dict:
    docs = [str(path.relative_to(SAMPLE)).replace("\\", "/") for path in SAMPLE.rglob("*") if path.is_file()]
    return {
        "name": "Reportly",
        "version": "2.6.0",
        "root": str(SAMPLE),
        "files": sorted(docs),
        "documents": [item for item in docs if item.startswith("docs/") or item.startswith("incidents/")],
    }


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
