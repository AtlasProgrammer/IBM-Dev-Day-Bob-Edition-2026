import unittest

from reportly.api import ReportlyAPI
from reportly.audit import reset_audit
from reportly.metrics import reset_metrics
from reportly.models import HttpRequest
from reportly.quotas import reset_quotas
from reportly.webhooks import reset_webhooks


class TestReportlyAPI(unittest.TestCase):
    def setUp(self) -> None:
        reset_audit()
        reset_metrics()
        reset_quotas()
        reset_webhooks()

    def tearDown(self) -> None:
        reset_audit()
        reset_metrics()
        reset_quotas()
        reset_webhooks()

    def test_missing_token_is_rejected(self) -> None:
        response = ReportlyAPI().handle(HttpRequest("POST", "/v1/exports", {}, "t1", b"a,b\n"))
        self.assertEqual(response.status, 401)

    def test_liveness_is_public(self) -> None:
        response = ReportlyAPI().handle(HttpRequest("GET", "/health/live", {}, "t2"))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["status"], "alive")

    def test_unknown_route_is_not_found(self) -> None:
        response = ReportlyAPI().handle(
            HttpRequest("GET", "/v1/missing", {"Authorization": "Bearer platform-ops"}, "t3")
        )
        self.assertEqual(response.status, 404)

    def test_export_unknown_tenant_is_rejected(self) -> None:
        response = ReportlyAPI().handle(
            HttpRequest(
                "POST",
                "/v1/exports",
                {"Authorization": "Bearer acme-live", "X-Tenant-Id": "ghost"},
                "t4",
                b"a,b\n",
            )
        )
        self.assertIn(response.status, (400, 403))
