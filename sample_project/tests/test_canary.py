import unittest

from reportly.config import settings
from reportly.release.canary import CanaryState, evaluate_probe


class TestCanary(unittest.TestCase):
    def setUp(self) -> None:
        self._flag = settings.migration_in_progress

    def tearDown(self) -> None:
        settings.migration_in_progress = self._flag

    def test_idle_probe_keeps_share(self) -> None:
        settings.migration_in_progress = False
        state = evaluate_probe(CanaryState(revision="rel-idle", share=10))
        self.assertFalse(state.rolled_back)
        self.assertEqual(state.share, 10)
        self.assertEqual(state.probes[0]["status"], 200)

    def test_migration_probe_is_recorded(self) -> None:
        settings.migration_in_progress = True
        state = evaluate_probe(CanaryState(revision="rel-2204", share=10))
        self.assertEqual(len(state.probes), 1)
        self.assertIn(state.probes[0]["status"], (200, 503))
