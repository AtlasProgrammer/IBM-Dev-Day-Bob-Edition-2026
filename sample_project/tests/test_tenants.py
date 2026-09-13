import unittest

from reportly.api import ReportlyAPI
from reportly.models import HttpRequest
from reportly.tenants import get_tenant, list_tenants


class TestTenants(unittest.TestCase):
    def test_catalog_has_regions_and_plans(self) -> None:
        acme = get_tenant("acme")
        self.assertIsNotNone(acme)
        assert acme is not None
        self.assertEqual(acme.plan, "enterprise")
        self.assertEqual(acme.region, "us-east")
        self.assertGreaterEqual(len(list_tenants()), 4)

    def test_tenant_directory_requires_auth(self) -> None:
        response = ReportlyAPI().handle(HttpRequest("GET", "/v1/tenants", {}, "tn-1"))
        self.assertEqual(response.status, 401)

    def test_tenant_directory_lists_public_fields(self) -> None:
        response = ReportlyAPI().handle(
            HttpRequest("GET", "/v1/tenants", {"Authorization": "Bearer platform-ops"}, "tn-2")
        )
        self.assertEqual(response.status, 200)
        ids = {item["id"] for item in response.body["tenants"]}
        self.assertTrue({"acme", "northwind", "demo", "platform"} <= ids)
