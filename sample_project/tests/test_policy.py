import unittest

from reportly.policy import evaluate


class TestPolicy(unittest.TestCase):
    def test_policy_holds_while_invariants_drift(self) -> None:
        result = evaluate(0, {"security": "PASS", "logic": "PASS"})
        self.assertFalse(result["allow_merge"])
        self.assertFalse(result["gates"]["invariants"])
        self.assertGreaterEqual(len(result["drift"]), 1)

    def test_failed_tests_block_merge(self) -> None:
        result = evaluate(2, {"security": "PASS"})
        self.assertFalse(result["gates"]["tests"])
