import unittest

from streamlit.testing.v1 import AppTest
from tests._streamlit_case import IsolatedWorldStateTestCase


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


class StreamlitV10Tests(IsolatedWorldStateTestCase):
    def setUp(self):
        super().setUp()
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def navigation(self):
        return [item for item in self.app.radio if item.label == "주요 메뉴"][0]

    def test_official_world_map_is_the_home_screen(self):
        self.assertEqual(self.app.session_state["active_view"], "World Map")
        self.assertEqual(
            self.navigation().options,
            [
                "학습 세계",
                "학습",
                "회복 학습",
                "도전 학습",
                "학습 분석",
                "인공지능",
                "학습 계획",
                "학습 자료실",
                "관리",
                "나의 학습",
            ],
        )

    def test_active_learning_view_preserves_v09_learning_flow(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["active_view"] = "Learning"
        self.app.run()
        self.assertEqual(self.app.session_state["active_view"], "Learning")
        answer_controls = [item for item in self.app.radio if item.label == "답을 선택하세요."]
        self.assertEqual(len(answer_controls), 1)

    def test_explicit_my_learning_navigation_does_not_clear_lesson(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.run()
        self.navigation().set_value("My Learning").run()
        self.assertEqual(self.app.session_state["active_view"], "My Learning")
        self.assertEqual(self.app.session_state["lesson"]["topic"], "Python")
        headers = [item.value for item in self.app.header]
        self.assertIn("나의 학습", headers)

    def test_my_learning_uses_completed_world_evidence(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["answer_confidence"] = {0: "high"}
        self.app.session_state["round_finished"] = True
        self.app.session_state["active_view"] = "Learning"
        self.app.run()
        self.navigation().set_value("My Learning").run()

        metrics = {item.label: item.value for item in self.app.metric}
        self.assertEqual(metrics["전체 정확도"], "100.0%")
        self.assertEqual(metrics["완료 라운드"], "1")
        subheaders = [item.value for item in self.app.subheader]
        self.assertIn("업적", subheaders)
        self.assertIn("장기 통계", subheaders)
        self.assertIn("최근 활동", subheaders)

    def test_recovery_has_a_controlled_empty_state(self):
        self.navigation().set_value("Recovery").run()
        headers = [item.value for item in self.app.header]
        self.assertIn("회복 학습", headers)
        info = [item.value for item in self.app.info]
        self.assertTrue(any("복습할 오답이 없습니다" in item for item in info))
        self.assertFalse(self.app.exception)

    def test_invalid_pending_world_context_is_repaired(self):
        self.app.session_state["pending_view"] = "bad"
        self.app.session_state["pending_learning_topic"] = 123
        self.app.session_state["pending_challenge"] = "bad"
        self.app.run()
        self.assertEqual(self.app.session_state["active_view"], "World Map")
        self.assertIsNone(self.app.session_state["pending_view"])
        self.assertIsNone(self.app.session_state["pending_learning_topic"])
        self.assertIsNone(self.app.session_state["pending_challenge"])


if __name__ == "__main__":
    unittest.main()
