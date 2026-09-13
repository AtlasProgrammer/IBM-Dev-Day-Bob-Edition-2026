from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from orchestra.paths import SAMPLE


def read_text(relative: str) -> str:
    path = SAMPLE / relative
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def loc(relative: str, needle: str) -> list[int]:
    lines = []
    for index, line in enumerate(read_text(relative).splitlines(), 1):
        if needle in line:
            lines.append(index)
    return lines


def cite(relative: str, needle: str) -> str:
    found = loc(relative, needle)
    if not found:
        return relative
    start = found[0]
    end = found[-1]
    if start == end:
        return f"{relative}:{start}"
    return f"{relative}:{start}-{end}"


def parse_python(relative: str) -> ast.AST | None:
    source = read_text(relative)
    if not source:
        return None
    try:
        return ast.parse(source)
    except SyntaxError:
        return None


def unbounded_reads(relative: str) -> list[dict]:
    tree = parse_python(relative)
    if tree is None:
        return []
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "read":
            continue
        if node.args or node.keywords:
            continue
        hits.append(
            {
                "rule": "unbounded-read",
                "file": relative,
                "line": getattr(node, "lineno", 0),
                "title": "Unbounded source.read()",
                "detail": "The call reads the entire stream into memory before any write starts.",
            }
        )
    return hits


def secret_logging(relative: str) -> list[dict]:
    source = read_text(relative)
    tree = parse_python(relative)
    if tree is None:
        return []
    hits = []
    lowered = source.lower()
    if "authorization" in lowered or "x-api-key" in lowered:
        if "redact_secrets" in source or "SENSITIVE_HEADERS" in source:
            line = loc(relative, "Authorization") or loc(relative, "authorization") or [1]
            hits.append(
                {
                    "rule": "secret-logging",
                    "file": relative,
                    "line": line[0],
                    "title": "Credential fields reach the logger",
                    "detail": "Request logging can persist Authorization or API keys when redaction is off.",
                }
            )
    return hits


def missing_tenant_bind(relative: str) -> list[dict]:
    source = read_text(relative)
    if "def require_token" not in source:
        return []
    if "tenant_mismatch" in source:
        return []
    line = loc(relative, "def require_token") or [1]
    return [
        {
            "rule": "tenant-bind",
            "file": relative,
            "line": line[0],
            "title": "Bearer tokens are not bound to a tenant",
            "detail": "require_token accepts any non-expired bearer and never compares it to X-Tenant-Id.",
        }
    ]


def readiness_blocks_migration(relative: str) -> list[dict]:
    source = read_text(relative)
    if "migration_in_progress" not in source:
        return []
    if "canary_ready_status" not in source and "503" not in source:
        return []
    line = loc(relative, "migration_in_progress") or [1]
    return [
        {
            "rule": "readiness-503",
            "file": relative,
            "line": line[0],
            "title": "Readiness fails during online migration",
            "detail": "Canary probes treat a migration as unready and drain the revision.",
        }
    ]


def parse_log_file(relative: str) -> dict:
    text = read_text(relative)
    errors = []
    secrets = []
    probes = []
    isolation = []
    for index, line in enumerate(text.splitlines(), 1):
        if "ERROR" in line or "MemoryError" in line:
            errors.append({"line": index, "text": line})
        if re.search(r"(Bearer |authorization=|x-api-key=)", line, re.I):
            secrets.append({"line": index, "text": line})
        if "status=503" in line or "rollback" in line:
            probes.append({"line": index, "text": line})
        if "cross_tenant" in line or "tenant.assumed" in line or "tenant.mismatch" in line:
            isolation.append({"line": index, "text": line})
    return {
        "file": relative,
        "errors": errors,
        "secrets": secrets,
        "probes": probes,
        "isolation": isolation,
        "lines": text.count("\n") + 1,
    }


def load_history() -> dict:
    path = SAMPLE / "vcs" / "history.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_blame() -> dict:
    path = SAMPLE / "vcs" / "blame.json"
    return json.loads(path.read_text(encoding="utf-8"))


def extract_constraints(relative: str) -> list[dict]:
    constraints = []
    for index, line in enumerate(read_text(relative).splitlines(), 1):
        stripped = line.strip()
        if re.search(r"\bMUST(?:\s+NOT)?\b", stripped):
            constraints.append({"file": relative, "line": index, "text": stripped.lstrip("- ").strip()})
    return constraints


def list_tests() -> list[str]:
    tests = SAMPLE / "tests"
    return sorted(path.name for path in tests.glob("test_*.py"))


def test_names(relative: str) -> list[str]:
    names = []
    tree = parse_python(relative)
    if tree is None:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            names.append(node.name)
    return names


def python_files() -> list[str]:
    files = []
    for path in (SAMPLE / "reportly").rglob("*.py"):
        files.append(str(path.relative_to(SAMPLE)).replace("\\", "/"))
    return sorted(files)


def existing_paths(items: list[str]) -> list[Path]:
    found = []
    for item in items:
        path = SAMPLE / item
        if path.exists():
            found.append(path)
    return found
