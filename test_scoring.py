import unittest
from scoring import normalize_scores, DIMENSIONS


class ScoringTests(unittest.TestCase):
    def test_sparse(self):
        score = normalize_scores({"total": 19})
        self.assertIsNone(score["total"])
        self.assertEqual(score["assessed_count"], 0)
        self.assertTrue(all(score[k]["score"] is None for k in DIMENSIONS))

    def test_conflicting_total_is_recalculated(self):
        score = normalize_scores({**{k: {"score": i, "reason": "A specific explanation of this dimension."} for i, k in enumerate(DIMENSIONS, 1)}, "total": 25})
        self.assertEqual(score["total"], 15)
        self.assertEqual(score["assessed_count"], 5)
        self.assertTrue(all(score[k]["status"] == "provisional" for k in DIMENSIONS))

    def test_missing_dimension(self):
        score = normalize_scores({k: {"score": 4, "reason": "A specific explanation of this dimension."} for k in DIMENSIONS[:-1]})
        self.assertIsNone(score["total"])
        self.assertEqual((score["assessed_count"], score["assessed_sum"]), (4, 16))

    def test_malformed_and_unsupported_status(self):
        for value in (True, "5", -1, 6, None, [], 3.5):
            self.assertIsNone(normalize_scores({"local_fit": {"score": value, "reason": "A specific explanation."}})["local_fit"]["score"])
        self.assertEqual(normalize_scores({"local_fit": {"score": 4, "reason": "A specific explanation.", "source": "verified", "status": "scored"}})["local_fit"]["status"], "provisional")

    def test_arabic_missing(self):
        self.assertIn("معلومات", normalize_scores({}, lang="ar")["local_fit"]["reason"])

    def test_legacy_fallback_scores_do_not_survive_recovery(self):
        legacy = {k: {"score": 3, "source": "fallback", "reason": "An old generic explanation."} for k in DIMENSIONS}
        self.assertIsNone(normalize_scores(legacy)["total"])
        self.assertEqual(normalize_scores(legacy)["assessed_count"], 0)
