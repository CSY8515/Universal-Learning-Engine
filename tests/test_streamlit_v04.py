import unittest

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


class StreamlitV04Tests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def test_v03_landing_controls_remain_available(self):
        self.assertEqual(self.app.title[0].value, "Universal Learning Engine")
        self.assertEqual(self.app.selectbox[0].options, ["5", "10", "15", "20"])
        self.assertEqual(
            self.app.selectbox[1].options, ["Easy", "Normal", "Hard", "Nightmare"]
        )
        self.assertEqual(self.app.button[0].label, "학습 시작")

    def test_confidence_control_is_optional_in_active_round(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.run()
        confidence = [
            item for item in self.app.selectbox if item.label == "답변 확신도 (선택)"
        ]
        self.assertEqual(len(confidence), 1)
        self.assertEqual(confidence[0].value, "선택 안 함")

    def test_submitted_answer_and_confidence_are_locked_during_feedback(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.run()

        answer = [item for item in self.app.radio if item.label == "답을 선택하세요."][0]
        confidence = [
            item for item in self.app.selectbox if item.label == "답변 확신도 (선택)"
        ][0]
        answer.set_value(0).run()
        confidence = [
            item for item in self.app.selectbox if item.label == "답변 확신도 (선택)"
        ][0]
        confidence.set_value("높음").run()
        confirm = [item for item in self.app.button if item.label == "정답 확인"][0]
        confirm.click().run()

        locked_answer = [
            item for item in self.app.radio if item.label == "답을 선택하세요."
        ][0]
        locked_confidence = [
            item for item in self.app.selectbox if item.label == "답변 확신도 (선택)"
        ][0]
        locked_confirm = [
            item for item in self.app.button if item.label == "정답 확인"
        ][0]
        self.assertTrue(locked_answer.disabled)
        self.assertTrue(locked_confidence.disabled)
        self.assertTrue(locked_confirm.disabled)
        self.assertEqual(self.app.session_state["answers"], {0: 0})
        self.assertEqual(self.app.session_state["answer_confidence"], {0: "high"})

    def test_completed_round_renders_adaptive_summary_without_hiding_result(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["answer_confidence"] = {0: "high"}
        self.app.session_state["round_finished"] = True
        self.app.run()

        headers = [item.value for item in self.app.header]
        subheaders = [item.value for item in self.app.subheader]
        self.assertIn("v0.4 적응형 학습 안내", headers)
        self.assertIn("라운드 결과 요약", subheaders)
        self.assertIn("다음 난이도 추천", subheaders)
        self.assertIn("회복 학습 추천", subheaders)
        self.assertFalse(self.app.exception)

    def test_recommended_difficulty_requires_explicit_click(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["answer_confidence"] = {0: "high"}
        self.app.session_state["round_finished"] = True
        self.app.run()

        difficulty_selector = [
            item for item in self.app.selectbox if item.label == "난이도를 선택하세요."
        ][0]
        self.assertEqual(difficulty_selector.value, "Easy")
        apply_buttons = [
            item for item in self.app.button if item.label == "추천 난이도 사용"
        ]
        self.assertEqual(len(apply_buttons), 1)
        apply_buttons[0].click().run()
        difficulty_selector = [
            item for item in self.app.selectbox if item.label == "난이도를 선택하세요."
        ][0]
        self.assertEqual(difficulty_selector.value, "Hard")
        self.assertEqual(self.app.session_state["lesson"]["topic"], "Python")

    def test_home_clears_session_adaptation(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["round_finished"] = True
        self.app.run()
        self.assertTrue(self.app.session_state["adaptation_records"])
        home = [item for item in self.app.button if item.label == "처음으로"]
        self.assertEqual(len(home), 1)
        home[0].click().run()
        self.assertEqual(self.app.session_state["adaptation_records"], {})
        self.assertIsNone(self.app.session_state["lesson"])


if __name__ == "__main__":
    unittest.main()
