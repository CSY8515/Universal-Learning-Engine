import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def make_lesson():
    return {
        "topic": "Python",
        "tutorial": "tutorial",
        "example": "example",
        "direct_task": "task",
        "practice": "practice",
        "difficulty": "Normal",
        "requested_question_count": 1,
        "cbt": [
            {
                "question": "Question",
                "choices": ["A", "B", "C", "D"],
                "answer_index": 0,
                "explanation": "explanation",
            }
        ],
    }


class StreamlitV05Tests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def complete_round(self, confidence="high"):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["answer_confidence"] = {0: confidence}
        self.app.session_state["round_finished"] = True
        self.app.run()

    def test_completed_round_adds_analytics_after_v04_result(self):
        self.complete_round()
        headers = [item.value for item in self.app.header]
        subheaders = [item.value for item in self.app.subheader]
        self.assertIn("v0.4 적응형 학습 안내", headers)
        self.assertIn("v0.5 학습 분석", headers)
        self.assertIn("라운드 결과 요약", subheaders)
        self.assertIn("최신 라운드 분석", subheaders)
        self.assertIn("세션 분석 — 현재 주제", subheaders)
        self.assertIn("전체 학습 분석 — 현재 세션", subheaders)
        self.assertIn("강점 / 약점 요약", subheaders)
        self.assertFalse(self.app.exception)

    def test_latest_round_metrics_match_completed_result(self):
        self.complete_round()
        metrics = {item.label: item.value for item in self.app.metric}
        self.assertEqual(metrics["정확도"], "100.0%")
        self.assertEqual(metrics["확신도 보고율"], "100.0%")
        self.assertEqual(metrics["근거 있는 성공"], "100.0%")
        self.assertEqual(metrics["확신한 오답"], "0.0%")

    def test_unset_confidence_remains_optional_in_analytics(self):
        self.complete_round(confidence=None)
        metrics = {item.label: item.value for item in self.app.metric}
        self.assertEqual(metrics["확신도 보고율"], "0.0%")
        self.assertFalse(self.app.exception)

    def test_analytics_adds_no_action_button(self):
        self.complete_round()
        labels = [item.label for item in self.app.button]
        self.assertIn("다시 학습", labels)
        self.assertIn("처음으로", labels)
        self.assertIn("추천 난이도 사용", labels)
        forbidden = {
            "자동 학습",
            "약점 점수 적용",
            "회복 일정 생성",
            "알림 생성",
        }
        self.assertFalse(forbidden.intersection(labels))

    def test_home_still_clears_analytics_source(self):
        self.complete_round()
        home = [item for item in self.app.button if item.label == "처음으로"][0]
        home.click().run()
        self.assertEqual(self.app.session_state["adaptation_records"], {})
        self.assertIsNone(self.app.session_state["lesson"])
        self.assertFalse(self.app.exception)

    def test_analytics_failure_does_not_hide_v04_result(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["answer_confidence"] = {0: "high"}
        self.app.session_state["round_finished"] = True
        with patch("analytics.build_learning_analytics", side_effect=RuntimeError("fail")):
            self.app.run()
        subheaders = [item.value for item in self.app.subheader]
        self.assertIn("라운드 결과 요약", subheaders)
        self.assertIn("다음 난이도 추천", subheaders)
        warnings = [item.value for item in self.app.warning]
        self.assertTrue(any("v0.5 학습 분석" in item for item in warnings))
        self.assertFalse(self.app.exception)


if __name__ == "__main__":
    unittest.main()
