import copy
import unittest

import analytics


def make_summary(
    round_id=1,
    topic="python",
    difficulty="Normal",
    correct=4,
    total=5,
    confidence=None,
    patterns=None,
    signals=None,
):
    confidence = confidence or {"low": 0, "medium": 1, "high": 4, "unset": 0}
    patterns = patterns or {
        "secure_success": 3,
        "developing_success": 1,
        "uncertain_success": 0,
        "confident_error": 1 if correct < total else 0,
        "developing_gap": 0,
        "recognized_gap": 0,
        "confidence_unknown": max(0, total - correct - (1 if correct < total else 0)),
    }
    return {
        "round_status": {
            "round_id": round_id,
            "topic_key": topic,
            "difficulty": difficulty,
            "question_count": total,
            "correct_count": correct,
            "wrong_count": total - correct,
            "accuracy": correct / total * 100,
            "confidence_counts": confidence,
            "answer_patterns": patterns,
        },
        "learning_patterns": signals
        or [{"name": "developing_understanding", "reason": "evidence"}],
        "difficulty_recommendation": {"recommended_difficulty": difficulty},
        "recovery_recommendation": {"priority": "medium"},
    }


class LearningAnalyticsTests(unittest.TestCase):
    def test_empty_analytics_is_valid(self):
        result = analytics.build_learning_analytics({}, "python")
        self.assertEqual(result["schema_version"], "0.5")
        self.assertEqual(result["overall"]["round_count"], 0)
        self.assertIsNone(result["overall"]["weighted_accuracy"])
        self.assertEqual(result["overall"]["learning_summary"]["status"], "empty")

    def test_round_analytics_reconciles_counts_and_does_not_mutate(self):
        source = make_summary()
        original = copy.deepcopy(source)
        result = analytics.build_round_analytics(source, 1)
        self.assertEqual(result["correct_count"], 4)
        self.assertEqual(result["wrong_count"], 1)
        self.assertEqual(result["accuracy"], 80.0)
        self.assertEqual(result["confidence"]["reporting_rate"], 100.0)
        self.assertEqual(result["answer_patterns"]["supported_success_rate"], 80.0)
        self.assertEqual(source, original)

    def test_weighted_accuracy_differs_from_mean_round_accuracy(self):
        records = {
            "python": [
                make_summary(round_id=1, correct=5, total=5),
                make_summary(
                    round_id=2,
                    correct=0,
                    total=15,
                    confidence={"low": 15, "medium": 0, "high": 0, "unset": 0},
                    patterns={
                        "secure_success": 0,
                        "developing_success": 0,
                        "uncertain_success": 0,
                        "confident_error": 0,
                        "developing_gap": 0,
                        "recognized_gap": 15,
                        "confidence_unknown": 0,
                    },
                ),
            ]
        }
        result = analytics.build_learning_analytics(records, "python")["current_topic"]
        self.assertEqual(result["weighted_accuracy"], 25.0)
        self.assertEqual(result["mean_round_accuracy"], 50.0)

    def test_current_topic_isolated_and_overall_includes_all_topics(self):
        records = {
            "python": [make_summary(topic="python")],
            "history": [make_summary(topic="history", round_id=2)],
        }
        result = analytics.build_learning_analytics(records, "python")
        self.assertEqual(result["current_topic"]["round_count"], 1)
        self.assertEqual(result["current_topic"]["topic_count"], 1)
        self.assertEqual(result["overall"]["round_count"], 2)
        self.assertEqual(result["overall"]["topic_count"], 2)
        self.assertEqual(result["overall"]["accuracy_direction"], "not_available")

    def test_topic_trend_and_repeated_signals_follow_record_order(self):
        records = {
            "python": [
                make_summary(round_id=1, correct=3),
                make_summary(round_id=2, correct=4),
            ]
        }
        result = analytics.build_learning_analytics(records, "python")["current_topic"]
        self.assertEqual(result["latest_change"], 20.0)
        self.assertEqual(result["accuracy_direction"], "improved")
        self.assertEqual(
            result["repeated_recent_signals"], ["developing_understanding"]
        )

    def test_one_round_has_no_comparison_trend(self):
        result = analytics.build_learning_analytics(
            {"python": [make_summary()]}, "python"
        )["current_topic"]
        self.assertIsNone(result["latest_change"])
        self.assertEqual(result["accuracy_direction"], "not_available")

    def test_unset_confidence_remains_unset(self):
        summary = make_summary(
            confidence={"low": 0, "medium": 0, "high": 0, "unset": 5},
            patterns={
                "secure_success": 0,
                "developing_success": 0,
                "uncertain_success": 0,
                "confident_error": 0,
                "developing_gap": 0,
                "recognized_gap": 0,
                "confidence_unknown": 5,
            },
        )
        result = analytics.build_round_analytics(summary, 1)
        self.assertEqual(result["confidence"]["counts"]["unset"], 5)
        self.assertEqual(result["confidence"]["reporting_rate"], 0.0)
        self.assertEqual(
            result["answer_patterns"]["counts"]["confidence_unknown"], 5
        )

    def test_strength_requires_two_rounds_and_ten_questions(self):
        strong_patterns = {
            "secure_success": 5,
            "developing_success": 0,
            "uncertain_success": 0,
            "confident_error": 0,
            "developing_gap": 0,
            "recognized_gap": 0,
            "confidence_unknown": 0,
        }
        one = [
            analytics.build_round_analytics(
                make_summary(correct=5, patterns=strong_patterns), 1
            )
        ]
        self.assertEqual(
            analytics.build_evidence_summaries(one)["insufficient_evidence"][0][
                "matched_rules"
            ],
            ["minimum_evidence_not_met"],
        )
        two = one + [
            analytics.build_round_analytics(
                make_summary(round_id=2, correct=5, patterns=strong_patterns), 2
            )
        ]
        result = analytics.build_evidence_summaries(two)
        self.assertEqual(len(result["strengths"]), 1)
        self.assertEqual(result["strengths"][0]["classification"], "strength")

    def test_strength_thresholds_include_exact_eighty_five_and_sixty(self):
        patterns = {
            "secure_success": 12,
            "developing_success": 0,
            "uncertain_success": 5,
            "confident_error": 0,
            "developing_gap": 3,
            "recognized_gap": 0,
            "confidence_unknown": 0,
        }
        rounds = [
            analytics.build_round_analytics(
                make_summary(
                    round_id=index,
                    correct=17,
                    total=20,
                    confidence={
                        "low": 5,
                        "medium": 3,
                        "high": 12,
                        "unset": 0,
                    },
                    patterns=patterns,
                ),
                index,
            )
            for index in (1, 2)
        ]
        strength = analytics.build_evidence_summaries(rounds)["strengths"][0]
        self.assertEqual(strength["weighted_accuracy"], 85.0)
        self.assertEqual(strength["supported_success_rate"], 60.0)

    def test_weakness_accuracy_and_confident_error_boundaries(self):
        low_patterns = {
            "secure_success": 0,
            "developing_success": 0,
            "uncertain_success": 2,
            "confident_error": 1,
            "developing_gap": 1,
            "recognized_gap": 1,
            "confidence_unknown": 0,
        }
        rounds = [
            analytics.build_round_analytics(
                make_summary(round_id=index, correct=2, patterns=low_patterns), index
            )
            for index in (1, 2)
        ]
        weakness = analytics.build_evidence_summaries(rounds)["weaknesses"][0]
        self.assertIn("low_weighted_accuracy", weakness["matched_rules"])
        self.assertIn("confident_error_evidence", weakness["matched_rules"])
        self.assertEqual(weakness["confident_error_rate"], 20.0)

    def test_exact_sixty_percent_is_not_low_accuracy_weakness(self):
        patterns = {
            "secure_success": 0,
            "developing_success": 3,
            "uncertain_success": 0,
            "confident_error": 0,
            "developing_gap": 2,
            "recognized_gap": 0,
            "confidence_unknown": 0,
        }
        rounds = [
            analytics.build_round_analytics(
                make_summary(round_id=index, correct=3, patterns=patterns), index
            )
            for index in (1, 2)
        ]
        evidence = analytics.build_evidence_summaries(rounds)
        self.assertFalse(evidence["weaknesses"])

    def test_invalid_and_duplicate_records_are_skipped_independently(self):
        records = {
            "python": [
                make_summary(round_id=1),
                make_summary(round_id=1),
                {"round_status": {}},
            ]
        }
        result = analytics.build_learning_analytics(records, "python")
        self.assertEqual(result["overall"]["round_count"], 1)
        self.assertEqual(result["overall"]["skipped_record_count"], 2)
        self.assertTrue(
            any("duplicate_round_id" in item for item in result["overall"]["issues"])
        )

    def test_missing_optional_counts_are_neutral_and_reported(self):
        summary = make_summary()
        del summary["round_status"]["confidence_counts"]
        del summary["round_status"]["answer_patterns"]
        result = analytics.build_round_analytics(summary, 1)
        self.assertEqual(result["confidence"]["counts"]["unset"], 5)
        self.assertEqual(
            result["answer_patterns"]["counts"]["confidence_unknown"], 5
        )
        self.assertIn("confidence_counts_missing", result["issues"])

    def test_difficulty_breakdowns_follow_supported_order(self):
        records = {
            "python": [
                make_summary(round_id=1, difficulty="Hard"),
                make_summary(round_id=2, difficulty="Easy"),
            ]
        }
        result = analytics.build_learning_analytics(records, "python")["current_topic"]
        self.assertEqual(
            [item["scope_key"] for item in result["difficulty_summaries"]],
            ["Easy", "Hard"],
        )

    def test_learning_summary_contains_counts_and_accuracy(self):
        result = analytics.build_learning_analytics(
            {"python": [make_summary()]}, "python"
        )["current_topic"]["learning_summary"]
        self.assertEqual(result["status"], "available")
        self.assertIn("4 of 5", result["headline"])
        self.assertTrue(any("weighted accuracy" in fact for fact in result["facts"]))


if __name__ == "__main__":
    unittest.main()
