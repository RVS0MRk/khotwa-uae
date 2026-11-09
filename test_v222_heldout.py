"""Acceptance thresholds for the immutable pre-detector evaluation fixture."""

import unittest
from pathlib import Path
from scripts.evaluate_v222_safety import evaluate


class V222HeldoutTests(unittest.TestCase):
    def test_frozen_heldout_acceptance_targets(self):
        report = evaluate(Path(__file__).parent / "tests/fixtures/v222_heldout.json")
        self.assertEqual(report["fixture_sha256"], "3265763ad3e6ae7efd4a23e265ff0cd5b1d0cf4ed52331b9b4c015f6ebe7525f")
        self.assertGreaterEqual(report["summary"]["unsafe"]["rate"], 0.9, report["summary"])
        self.assertEqual(report["summary"]["safe"]["rate"], 1, report["summary"])
