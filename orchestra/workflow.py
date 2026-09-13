from __future__ import annotations

PHASES = [
    {
        "id": "understand",
        "label": "Understand",
        "bob": "Document understanding",
        "agents": ["document-analyst"],
    },
    {
        "id": "investigate",
        "label": "Investigate",
        "bob": "Parallel tasks / subagents",
        "agents": ["code-investigator", "log-analyst", "git-historian", "test-engineer"],
    },
    {
        "id": "synthesize",
        "label": "Synthesize",
        "bob": "Agent Mode",
        "agents": ["orchestrator"],
    },
    {
        "id": "fix",
        "label": "Fix",
        "bob": "Agent Mode",
        "agents": ["orchestrator"],
    },
    {
        "id": "verify",
        "label": "Verify",
        "bob": "Verification loop",
        "agents": ["test-engineer", "code-reviewer"],
    },
    {
        "id": "release",
        "label": "Release",
        "bob": "Release decision",
        "agents": ["release-officer"],
    },
]


def public_workflow() -> dict:
    return {
        "name": "incident-to-merge",
        "phases": PHASES,
        "parallel": ["code-investigator", "log-analyst", "git-historian", "test-engineer"],
    }
