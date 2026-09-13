# Runbook — export MemoryError

Symptom: `POST /v1/exports` returns HTTP 500. Logs show `error=MemoryError`.

1. Confirm report size in `reportly.export` logs (`export.size` or `bytes=`).
2. Inspect `reportly/export/service.py` for a full-buffer `source.read()`.
3. Compare with `reportly/export/streaming.py`, which still implements chunked reads.
4. Check ADR 0003 — the in-memory refactor is the usual regression window.
5. Restore streaming, add a source that raises `MemoryError` on unbounded `read()`, and refuse the merge if that test is absent.
