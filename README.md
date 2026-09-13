# ORCHESTRA — IBM Bob 2.0 Engineering Orchestrator

Hackathon prototype for the IBM Bob 2.0 challenge: turn a production incident into a verified merge decision.

```
Incident → document understanding → parallel subagents → root cause → fix → tests → review → release gate
```

The problem it attacks is the expensive middle of debugging, review, testing, maintenance, and release: engineers reread tickets, ADRs, logs, blame, and tests by hand, then rework the same defect because a guard was never added. ORCHESTRA runs those steps as one workflow on a real sample platform (Reportly) and shows the time and error reduction.

## Run

Requires Python 3.10+. No third-party packages.

```bash
python app.py
```

Open http://127.0.0.1:8000

## Demo

1. Pick an incident: export OOM, secret logging, canary rollback, or cross-tenant export.
2. Run investigation and watch Document, Code, Logs, Git, and Test agents complete.
3. Inspect the cited root cause.
4. Generate the fix plan, then validate it. Validation copies Reportly, applies the patch, and runs the real unittest suite.
5. Show readiness, review axes, and the manual-vs-ORCHESTRA time comparison.

## IBM Bob 2.0 mapping

| Bob capability | In this prototype |
|---|---|
| Agent Mode | `agents/orchestrator.md` owns the incident-to-merge loop |
| Parallel tasks / subagents | Code, logs, git, and tests investigate at the same time |
| Document understanding | Architecture, ADRs, runbooks, security, onboarding, tickets |
| Verification | Isolated patch + regression tests + multi-axis review + merge gate |

`agents/*.md` are the Bob skill prompts. The Python backend is a deterministic local harness so the demo runs without credentials.

## Sample project

`sample_project/` is Reportly 2.6 — a multi-tenant export platform with quotas, feature flags, audit, webhooks, and canary probes. Four planted defects violate written invariants so the orchestrator has production-shaped work, not a toy function.
