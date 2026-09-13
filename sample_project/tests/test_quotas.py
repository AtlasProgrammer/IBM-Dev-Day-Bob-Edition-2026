import unittest

from reportly.quotas import QuotaExceeded, consume, reset_quotas, snapshot


class TestQuotas(unittest.TestCase):
    def setUp(self) -> None:
        reset_quotas()

    def tearDown(self) -> None:
        reset_quotas()

    def test_consume_tracks_remaining(self) -> None:
        first = consume("demo", 10)
        self.assertEqual(first.used_bytes, 10)
        self.assertEqual(first.remaining_bytes, snapshot("demo").remaining_bytes)

    def test_unknown_tenant_has_zero_limit(self) -> None:
        snap = snapshot("ghost")
        self.assertEqual(snap.monthly_bytes, 0)

    def test_exceeding_trial_quota_raises(self) -> None:
        consume("demo", 40_000_000)
        with self.assertRaises(QuotaExceeded):
            consume("demo", 20_000_000)
