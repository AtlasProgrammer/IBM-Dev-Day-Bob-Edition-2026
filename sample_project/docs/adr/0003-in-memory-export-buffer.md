# ADR 0003 — In-memory export buffering

Status: Accepted (2026-07-12)

## Decision

`ExportService` now reads the entire report into memory before formatting and writing. The previous `StreamingExporter` path remains in the repository but is no longer wired into the API.

## Why

Syscall overhead on 2–5 MB interactive exports looked high in staging flame graphs. Buffering simplified the formatter contract.

## Consequences

- Peak RSS now scales with report size.
- Scheduled 700 MB+ tenant exports were not re-benchmarked.
- Architecture invariant "bounded memory" is no longer enforced by the implementation.
