from __future__ import annotations

import json
import sys

from reportly import __version__
from reportly.api import ReportlyAPI
from reportly.flags import drift
from reportly.metrics import snapshot as metrics_snapshot
from reportly.models import HttpRequest
from reportly.tenants import list_tenants, public_tenant


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    api = ReportlyAPI()
    if not args or args[0] == "info":
        print(f"reportly {__version__}")
        return 0
    if args[0] == "health":
        live = api.handle(HttpRequest("GET", "/health/live", {}, "cli-live"))
        ready = api.handle(HttpRequest("GET", "/health/ready", {}, "cli-ready"))
        print(live.status, live.body)
        print(ready.status, ready.body)
        return 0 if live.status == 200 and ready.status == 200 else 1
    if args[0] == "doctor":
        items = drift()
        print(json.dumps({"version": __version__, "drift": items, "healthy": not items}, indent=2))
        return 0 if not items else 1
    if args[0] == "tenants":
        print(json.dumps([public_tenant(item) for item in list_tenants()], indent=2))
        return 0
    if args[0] == "metrics":
        request = HttpRequest("GET", "/v1/metrics", {"Authorization": "Bearer platform-ops", "X-Tenant-Id": "platform"}, "cli-metrics")
        response = api.handle(request)
        print(response.status, metrics_snapshot())
        return 0 if response.status < 400 else 1
    if args[0] == "export":
        body = b"id,name\n1,acme\n"
        request = HttpRequest(
            "POST",
            "/v1/exports",
            {
                "Authorization": "Bearer demo-token",
                "X-Report-Id": "rpt-demo",
                "X-Tenant-Id": "demo",
                "X-Export-Format": "csv",
            },
            "cli-export",
            body,
        )
        response = api.handle(request)
        print(response.status, response.body)
        return 0 if response.status < 400 else 1
    sys.stderr.write("usage: python -m reportly [info|health|doctor|tenants|metrics|export]\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
