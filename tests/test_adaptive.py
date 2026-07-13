import copy
import unittest

import adaptive


def make_answers(correct_count, total=5, confidence="high"):
    return [
        {"is_correct": index < correct_count, "confidence": confidence}
        for index in range(total)
    ]


class AdaptiveRuleTests(unittest.TestCase):
    def status(self, correct, difficulty="Normal", confidence="high", total=5):
        return adaptive.build_round_status(
            make_answers(correct, total, confidence), difficulty, 1, "python"
        )

    def test_confidence_categories(self):
        expected = {
            (True, "high"): "secure_success",
            (True, "medium"): "developing_success",
            (True, "low"): "uncertain_success",
            (False, "high"): "confident_error",
            (False, "medium"): "developing_gap",
            (False, "low"): "recognized_gap",
            (True, None): "confidence_unknown",
            (False, "invalid"): "confidence_unknown",
        }
        for inputs, category in expected.items():
            with self.subTest(inputs=inputs):
                self.assertEqual(adaptive.confidence_category(*inputs), category)

    def test_round_status_metrics_and_no_input_mutation(self):
        answers = make_answers(3, confidence="medium")
        original = copy.deepcopy(answers)
        status = adaptive.build_round_status(answers, "Normal", 4, "python")
        self.assertEqual(status["accuracy"], 60)
        self.assertEqual(status["correct_count"], 3)
        self.assertEqual(status["wrong_count"], 2)
        self.assertEqual(status["confidence_counts"]["medium"], 5)
        self.assertEqual(answers, original)

    def test_round_status_rejects_empty_or_bad_difficulty(self):
        with self.assertRaises(ValueError):
            adaptive.build_round_status([], "Normal", 1, "python")
        with self.assertRaises(ValueError):
            adaptive.build_round_status(make_answers(5), "Impossible", 1, "python")

    def test_difficulty_thresholds_and_one_level_bounds(self):
        cases = [
            (2, "Hard", "Normal"),
            (3, "Normal", "Normal"),
            (4, "Normal", "Normal"),
            (17, "Normal", "Hard"),
            (5, "Nightmare", "Nightmare"),
            (2, "Easy", "Easy"),
        ]
        for correct, current, recommended in cases:
            total = 20 if correct == 17 else 5
            with self.subTest(correct=correct, current=current):
                status = self.status(correct, current, total=total)
                result = adaptive.recommend_difficulty(status)
                self.assertEqual(result["recommended_difficulty"], recommended)
                self.assertIn("advisory", result)

    def test_high_accuracy_without_confidence_stays(self):
        status = self.status(5, confidence=None)
        result = adaptive.recommend_difficulty(status)
        self.assertEqual(result["recommended_difficulty"], "Normal")
        self.assertEqual(result["rule"], "high_accuracy_limited_confidence")

    def test_pattern_signals_and_mutual_exclusion(self):
        strong = adaptive.analyze_learning_patterns(self.status(5))
        fragile = adaptive.analyze_learning_patterns(self.status(5, confidence=None))
        self.assertIn("strong_mastery_signal", {item["name"] for item in strong})
        fragile_names = {item["name"] for item in fragile}
        self.assertIn("fragile_success_signal", fragile_names)
        self.assertNotIn("strong_mastery_signal", fragile_names)

    def test_overconfidence_can_accompany_other_signal(self):
        status = self.status(3, confidence="high")
        names = {item["name"] for item in adaptive.analyze_learning_patterns(status)}
        self.assertEqual(names, {"developing_understanding", "overconfidence_risk"})

    def test_recovery_priority_precedence(self):
        medium_status = self.status(4, confidence="medium")
        medium = adaptive.build_adaptive_summary(medium_status)
        self.assertEqual(medium["recovery_recommendation"]["priority"], "medium")

        high_status = self.status(4, confidence="high")
        high = adaptive.build_adaptive_summary(high_status)
        self.assertEqual(high["recovery_recommendation"]["priority"], "high")
        self.assertIn("No reminder", high["recovery_recommendation"]["advisory"])

    def test_summary_contains_explanations(self):
        summary = adaptive.build_adaptive_summary(self.status(5))
        self.assertTrue(summary["difficulty_recommendation"]["reason"])
        self.assertTrue(summary["recovery_recommendation"]["reason"])
        self.assertTrue(summary["learning_patterns"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
