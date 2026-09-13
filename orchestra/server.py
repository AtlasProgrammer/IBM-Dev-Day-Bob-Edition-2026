from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from orchestra.catalog import CAPABILITIES, get_incident, list_incidents, list_skills, project_index
from orchestra.engine import investigate, plan_fix, run_validation
from orchestra.impact import estimate
from orchestra.paths import WEB
from orchestra.workflow import public_workflow


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return None

    def _send(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: object, status: int = 200) -> None:
        self._send(_json_bytes(payload), "application/json; charset=utf-8", status)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        incident_id = (query.get("id") or ["BUG-1842"])[0]
        if path == "/api/catalog":
            self._send_json(
                {
                    "incidents": list_incidents(),
                    "capabilities": CAPABILITIES,
                    "project": project_index(),
                }
            )
            return
        if path == "/api/skills":
            self._send_json({"skills": list_skills()})
            return
        if path == "/api/workflow":
            self._send_json(public_workflow())
            return
        if path == "/api/impact":
            try:
                self._send_json(estimate(get_incident(incident_id)))
            except KeyError:
                self._send_json({"error": "unknown_incident"}, 404)
            return
        if path == "/api/investigate":
            try:
                self._send_json(investigate(incident_id))
            except KeyError:
                self._send_json({"error": "unknown_incident"}, 404)
            return
        if path == "/api/fix":
            try:
                self._send_json(plan_fix(incident_id))
            except KeyError:
                self._send_json({"error": "unknown_incident"}, 404)
            return
        if path == "/api/validate":
            try:
                self._send_json(run_validation(incident_id))
            except KeyError:
                self._send_json({"error": "unknown_incident"}, 404)
            return
        if path == "/api/stream":
            self._stream(incident_id)
            return
        self._static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        body = self._read_json()
        incident_id = body.get("id") or "BUG-1842"
        if parsed.path == "/api/fix":
            try:
                self._send_json(plan_fix(incident_id))
            except KeyError:
                self._send_json({"error": "unknown_incident"}, 404)
            return
        if parsed.path == "/api/validate":
            try:
                self._send_json(run_validation(incident_id))
            except KeyError:
                self._send_json({"error": "unknown_incident"}, 404)
            return
        self._send_json({"error": "not_found"}, 404)

    def _stream(self, incident_id: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        def emit(event: str, data: dict) -> None:
            payload = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            self.wfile.write(payload.encode("utf-8"))
            self.wfile.flush()

        try:
            investigate(incident_id, emit=emit)
        except KeyError:
            emit("error", {"error": "unknown_incident"})

    def _static(self, path: str) -> None:
        mapping = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/index.html": ("index.html", "text/html; charset=utf-8"),
            "/styles.css": ("styles.css", "text/css; charset=utf-8"),
            "/app.js": ("app.js", "application/javascript; charset=utf-8"),
        }
        if path not in mapping:
            self._send(_json_bytes({"error": "not_found"}), "application/json; charset=utf-8", 404)
            return
        name, content_type = mapping[path]
        body = (WEB / name).read_bytes()
        self._send(body, content_type)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"ORCHESTRA running at http://{host}:{port}")
    server.serve_forever()
