import unittest

from reportly.config import settings
from reportly.models import HttpRequest
from reportly.observability import dump_logs, log_request, reset_logs


class TestObservability(unittest.TestCase):
    def setUp(self) -> None:
        reset_logs()
        self._headers = settings.log_request_headers
        self._redact = settings.redact_secrets

    def tearDown(self) -> None:
        settings.log_request_headers = self._headers
        settings.redact_secrets = self._redact
        reset_logs()

    def test_request_logger_emits_path(self) -> None:
        settings.log_request_headers = False
        log_request(HttpRequest("GET", "/v1/exports", {"X-Request": "1"}, "obs-1"))
        text = "\n".join(dump_logs())
        self.assertIn("/v1/exports", text)
