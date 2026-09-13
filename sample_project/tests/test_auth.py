import unittest

from reportly.api import ReportlyAPI
from reportly.auth import REGISTRY, extract_bearer, resolve_identity
from reportly.models import HttpRequest


class TestAuth(unittest.TestCase):
    def test_extract_bearer_strips_prefix(self) -> None:
        request = HttpRequest("GET", "/v1/exports", {"Authorization": "Bearer acme-live"}, "a1")
        self.assertEqual(extract_bearer(request), "acme-live")

    def test_registry_contains_platform_identities(self) -> None:
        self.assertIn("acme-live", REGISTRY)
        self.assertEqual(REGISTRY["northwind-live"].tenant_id, "northwind")

    def test_unknown_token_still_resolves_empty(self) -> None:
        request = HttpRequest("GET", "/v1/exports", {"Authorization": "Bearer ghost-token"}, "a2")
        self.assertIsNone(resolve_identity(request))

    def test_expired_token_is_rejected(self) -> None:
        response = ReportlyAPI().handle(
            HttpRequest("POST", "/v1/exports", {"Authorization": "Bearer expired-1"}, "a3", b"a,b\n")
        )
        self.assertEqual(response.status, 401)
        self.assertEqual(response.body["error"], "expired_token")
