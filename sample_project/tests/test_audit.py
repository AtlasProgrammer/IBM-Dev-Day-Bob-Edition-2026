import unittest

from reportly.api import ReportlyAPI
from reportly.audit import reset_audit, trail
from reportly.metrics import reset_metrics
from reportly.models import HttpRequest
from reportly.quotas import reset_quotas
from reportly.webhooks import pending, reset_webhooks


class TestAuditAndSideEffects(unittest.TestCase):
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

    def test_export_writes_audit_and_webhook(self) -> None:
        response = ReportlyAPI().handle(
            HttpRequest(
                "POST",
                "/v1/exports",
                {
                    "Authorization": "Bearer acme-live",
                    "X-Tenant-Id": "acme",
                    "X-Report-Id": "rpt-acme",
                    "X-Export-Format": "csv",
                },
                "aud-1",
                b"id,name\n1,acme\n",
            )
        )
        self.assertEqual(response.status, 201)
        events = trail("acme")
        self.assertEqual(events[0].event, "export.requested")
        self.assertEqual(events[0].fields.get("token_tenant"), "acme")
        self.assertEqual(pending()[0]["topic"], "export.completed")
