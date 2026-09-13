from __future__ import annotations

import json


class ReportFormatter:
    def render(self, payload: bytes, fmt: str) -> bytes:
        if fmt == "json":
            data = json.loads(payload.decode("utf-8"))
            return json.dumps(data, separators=(",", ":")).encode("utf-8")
        return payload

    def render_chunk(self, chunk: bytes, fmt: str) -> bytes:
        return chunk
