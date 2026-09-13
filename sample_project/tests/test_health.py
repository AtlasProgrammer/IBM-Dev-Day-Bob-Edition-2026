import unittest

from reportly.config import settings
from reportly.release.health import liveness, readiness


class TestHealth(unittest.TestCase):
    def setUp(self) -> None:
        self._flag = settings.migration_in_progress

    def tearDown(self) -> None:
        settings.migration_in_progress = self._flag

    def test_liveness_when_idle(self) -> None:
        settings.migration_in_progress = False
        status, body = liveness()
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "alive")

    def test_readiness_when_idle(self) -> None:
        settings.migration_in_progress = False
        status, body = readiness()
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ready")
