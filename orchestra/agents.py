from __future__ import annotations

import time
from typing import Callable

from orchestra import analyze
from orchestra.catalog import Incident


def _pack(agent_id: str, name: str, findings: list[dict], evidence: list[str], duration: float) -> dict:
    return {
        "id": agent_id,
        "agent": name,
        "skill": f"agents/{agent_id}.md",
        "status": "PASS",
        "duration_ms": int(duration * 1000),
        "findings": findings,
        "evidence": evidence,
    }


def document_analyst(incident: Incident) -> dict:
    started = time.perf_counter()
    time.sleep(0.35)
    docs = [item for item in incident.focus if item.endswith(".md") or item.startswith("docs/")]
    if f"incidents/{incident.id}.md" not in docs:
        docs.append(f"incidents/{incident.id}.md")
    constraints = []
    for doc in docs:
        constraints.extend(analyze.extract_constraints(doc))
    findings = []
    if incident.id == "BUG-1842":
        findings.append(
            {
                "severity": "HIGH",
                "title": "Architecture requires bounded memory",
                "detail": "architecture.md and the export runbook both forbid full-buffer exports. ADR 0003 accepted the opposite tradeoff.",
                "file": "docs/architecture.md",
                "lines": [line["line"] for line in constraints if "bounded memory" in line["text"].lower()],
            }
        )
    elif incident.id == "BUG-1901":
        findings.append(
            {
                "severity": "HIGH",
                "title": "Secret-logging invariant is already written down",
                "detail": "Architecture forbids credentials in logs. ADR 0005 rolled staging header dumps into production.",
                "file": "docs/architecture.md",
                "lines": [line["line"] for line in constraints if "MUST NOT" in line["text"]],
            }
        )
    elif incident.id == "TEN-2044":
        findings.append(
            {
                "severity": "HIGH",
                "title": "Tokens must be bound to one tenant",
                "detail": "security.md, onboarding, and architecture require HTTP 403 on a tenant mismatch. ADR 0007 trusted the caller header instead.",
                "file": "docs/security.md",
                "lines": [line["line"] for line in constraints if "tenant" in line["text"].lower()],
            }
        )
    else:
        findings.append(
            {
                "severity": "HIGH",
                "title": "Readiness must stay 200 during online migrations",
                "detail": "The canary runbook and architecture treat a 503 on /health/ready as a failed deploy, not a healthy migration signal.",
                "file": "docs/architecture.md",
                "lines": [line["line"] for line in constraints if "ready" in line["text"].lower()],
            }
        )
    evidence = [analyze.cite(doc, "MUST") for doc in docs if analyze.read_text(doc)]
    if not evidence:
        evidence = docs
    return _pack("document-analyst", "Document Analyst", findings, evidence, time.perf_counter() - started)


def code_investigator(incident: Incident) -> dict:
    started = time.perf_counter()
    time.sleep(0.55)
    findings = []
    evidence = []
    if incident.id == "BUG-1842":
        for hit in analyze.unbounded_reads("reportly/export/service.py"):
            findings.append(
                {
                    "severity": "HIGH",
                    "title": hit["title"],
                    "detail": f"{hit['detail']} StreamingExporter in reportly/export/streaming.py still implements the safe path.",
                    "file": hit["file"],
                    "lines": [hit["line"]],
                }
            )
            evidence.append(f"{hit['file']}:{hit['line']}")
        evidence.append(analyze.cite("reportly/export/streaming.py", "read(self.chunk_size)"))
        evidence.append(analyze.cite("reportly/flags.py", "stream_exports"))
    elif incident.id == "BUG-1901":
        for hit in analyze.secret_logging("reportly/observability.py"):
            findings.append(
                {
                    "severity": "HIGH",
                    "title": hit["title"],
                    "detail": hit["detail"],
                    "file": hit["file"],
                    "lines": [hit["line"]],
                }
            )
            evidence.append(f"{hit['file']}:{hit['line']}")
        evidence.append(analyze.cite("reportly/config.py", "redact_secrets"))
    elif incident.id == "TEN-2044":
        for hit in analyze.missing_tenant_bind("reportly/auth.py"):
            findings.append(
                {
                    "severity": "HIGH",
                    "title": hit["title"],
                    "detail": hit["detail"],
                    "file": hit["file"],
                    "lines": [hit["line"]],
                }
            )
            evidence.append(f"{hit['file']}:{hit['line']}")
        evidence.append(analyze.cite("reportly/api.py", "X-Tenant-Id"))
        evidence.append(analyze.cite("reportly/flags.py", "bind_token_tenant"))
    else:
        for hit in analyze.readiness_blocks_migration("reportly/release/health.py"):
            findings.append(
                {
                    "severity": "HIGH",
                    "title": hit["title"],
                    "detail": hit["detail"],
                    "file": hit["file"],
                    "lines": [hit["line"]],
                }
            )
            evidence.append(f"{hit['file']}:{hit['line']}")
        evidence.append(analyze.cite("reportly/release/migrate.py", "migration_in_progress"))
        evidence.append(analyze.cite("reportly/release/canary.py", "readiness_failed"))
    return _pack("code-investigator", "Code Investigator", findings, evidence, time.perf_counter() - started)


def log_analyst(incident: Incident) -> dict:
    started = time.perf_counter()
    time.sleep(0.45)
    findings = []
    evidence = []
    if incident.id == "BUG-1842":
        parsed = analyze.parse_log_file("logs/application.log")
        if parsed["errors"]:
            first = parsed["errors"][0]
            findings.append(
                {
                    "severity": "HIGH",
                    "title": "Out-of-memory failure at the export boundary",
                    "detail": first["text"],
                    "file": parsed["file"],
                    "lines": [item["line"] for item in parsed["errors"]],
                }
            )
            evidence.append(f"{parsed['file']}:{first['line']}")
    elif incident.id == "BUG-1901":
        parsed = analyze.parse_log_file("logs/access.log")
        if parsed["secrets"]:
            first = parsed["secrets"][0]
            findings.append(
                {
                    "severity": "HIGH",
                    "title": "Live credentials in access logs",
                    "detail": "Authorization and API key values are stored in plaintext next to the request id.",
                    "file": parsed["file"],
                    "lines": [item["line"] for item in parsed["secrets"]],
                }
            )
            evidence.append(f"{parsed['file']}:{first['line']}")
    elif incident.id == "TEN-2044":
        parsed = analyze.parse_log_file("logs/tenant-isolation.log")
        if parsed["isolation"]:
            first = parsed["isolation"][0]
            findings.append(
                {
                    "severity": "HIGH",
                    "title": "Cross-tenant export recorded in audit",
                    "detail": first["text"],
                    "file": parsed["file"],
                    "lines": [item["line"] for item in parsed["isolation"]],
                }
            )
            evidence.append(f"{parsed['file']}:{first['line']}")
    else:
        parsed = analyze.parse_log_file("logs/deploy-canary.log")
        if parsed["probes"]:
            first = parsed["probes"][0]
            findings.append(
                {
                    "severity": "HIGH",
                    "title": "Canary drained after readiness 503",
                    "detail": first["text"],
                    "file": parsed["file"],
                    "lines": [item["line"] for item in parsed["probes"]],
                }
            )
            evidence.append(f"{parsed['file']}:{first['line']}")
    return _pack("log-analyst", "Log Analyst", findings, evidence, time.perf_counter() - started)


def git_historian(incident: Incident) -> dict:
    started = time.perf_counter()
    time.sleep(0.3)
    history = analyze.load_history()
    blame = analyze.load_blame()
    wanted = {
        "BUG-1842": "81f92a",
        "BUG-1901": "c3e118",
        "REL-2204": "e71bb2",
        "TEN-2044": "a91c03",
    }[incident.id]
    commit = next(item for item in history["commits"] if item["sha"] == wanted)
    target = {
        "BUG-1842": "reportly/export/service.py",
        "BUG-1901": "reportly/observability.py",
        "REL-2204": "reportly/release/health.py",
        "TEN-2044": "reportly/auth.py",
    }[incident.id]
    note = blame.get(target, {})
    findings = [
        {
            "severity": "MEDIUM",
            "title": f"Regression window {commit['sha']}",
            "detail": f"{commit['title']}. {commit['summary']}",
            "file": target,
            "lines": [],
        }
    ]
    evidence = [f"vcs/history.json:{commit['sha']}", f"vcs/blame.json:{target}"]
    if note.get("note"):
        findings[0]["detail"] += f" Blame: {note['note']}"
    return _pack("git-historian", "Git Historian", findings, evidence, time.perf_counter() - started)


def test_engineer(incident: Incident) -> dict:
    started = time.perf_counter()
    time.sleep(0.4)
    existing = []
    for name in analyze.list_tests():
        existing.extend(analyze.test_names(f"tests/{name}"))
    missing = {
        "BUG-1842": [
            "test_large_export_uses_bounded_reads",
            "test_export_survives_full_read_bomb",
        ],
        "BUG-1901": [
            "test_authorization_header_is_redacted",
            "test_api_key_is_redacted",
        ],
        "REL-2204": [
            "test_readiness_stays_ready_during_migration",
        ],
        "TEN-2044": [
            "test_cross_tenant_export_is_forbidden",
            "test_token_is_bound_to_tenant",
        ],
    }[incident.id]
    present = [name for name in missing if name in existing]
    absent = [name for name in missing if name not in existing]
    findings = [
        {
            "severity": "MEDIUM",
            "title": "Regression coverage gap",
            "detail": f"Existing tests: {', '.join(existing) or 'none'}. Missing: {', '.join(absent)}.",
            "file": "tests/",
            "lines": [],
        }
    ]
    evidence = [f"tests/{name}" for name in analyze.list_tests()]
    if present:
        findings[0]["detail"] += " Some expected guards already exist."
    return _pack("test-engineer", "Test Engineer", findings, evidence, time.perf_counter() - started)


def code_reviewer(incident: Incident, patch: dict | None = None, tests: dict | None = None) -> dict:
    started = time.perf_counter()
    time.sleep(0.25)
    files = [item["file"] for item in (patch or {}).get("changes", [])]
    after = (tests or {}).get("after_fix", {})
    passed = after.get("failed", 1) == 0 and after.get("total", 0) > 0
    review = {
        "security": "PASS" if incident.id not in {"BUG-1901", "TEN-2044"} or any(
            name in item for item in files for name in ("observability.py", "auth.py")
        ) else "HOLD",
        "logic": "PASS" if passed else "HOLD",
        "performance": "PASS" if incident.id != "BUG-1842" or any("service.py" in item for item in files) else "HOLD",
        "tests": "PASS" if any("test_" in item for item in files) or passed else "HOLD",
        "architecture": "PASS" if passed else "HOLD",
    }
    findings = [
        {
            "severity": "LOW" if all(value == "PASS" for value in review.values()) else "MEDIUM",
            "title": "Multi-axis review",
            "detail": ", ".join(f"{key}={value}" for key, value in review.items()),
            "file": "review",
            "lines": [],
        }
    ]
    payload = _pack("code-reviewer", "Code Reviewer", findings, list(files) or ["review"], time.perf_counter() - started)
    payload["review"] = review
    return payload


def release_officer(incident: Incident, tests: dict | None = None, review: dict | None = None) -> dict:
    started = time.perf_counter()
    time.sleep(0.2)
    after = (tests or {}).get("after_fix", {})
    axes = (review or {}).get("review", {})
    ready = after.get("failed", 1) == 0 and after.get("total", 0) > 0 and all(value == "PASS" for value in axes.values())
    score = 96 if ready else 54
    findings = [
        {
            "severity": "LOW" if ready else "HIGH",
            "title": "READY TO MERGE" if ready else "HOLD MERGE",
            "detail": "Validation, review, and workflow invariants agree." if ready else "A required axis is still red.",
            "file": "release",
            "lines": [],
        }
    ]
    payload = _pack("release-officer", "Release Officer", findings, [incident.id], time.perf_counter() - started)
    payload["readiness"] = score
    payload["decision"] = "READY TO MERGE" if ready else "HOLD MERGE"
    return payload


PARALLEL_INVESTIGATORS: list[Callable[[Incident], dict]] = [
    code_investigator,
    log_analyst,
    git_historian,
    test_engineer,
]
