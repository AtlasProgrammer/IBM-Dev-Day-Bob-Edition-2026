import unittest

from reportly.api import ReportlyAPI
from reportly.flags import drift, flags
from reportly.models import HttpRequest


class TestFlags(unittest.TestCase):
    def test_production_flags_drift_from_architecture(self) -> None:
        names = {item["flag"] for item in drift()}
        self.assertIn("stream_exports", names)
        self.assertIn("bind_token_tenant", names)
        self.assertFalse(flags.stream_exports)
        self.assertFalse(flags.bind_token_tenant)

    def test_internal_drift_endpoint_is_public(self) -> None:
        response = ReportlyAPI().handle(HttpRequest("GET", "/internal/drift", {}, "fl-1"))
        self.assertEqual(response.status, 200)
        self.assertGreaterEqual(len(response.body["drift"]), 1)
