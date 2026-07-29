import unittest
from datetime import date

from streamlit.testing.v1 import AppTest

import world_state
from tests._streamlit_case import IsolatedWorldStateTestCase


def make_lesson():
    return {
        "topic": "Python",
        "tutorial": "tutorial",
        "example": "example",
        "direct_task": "task",
        "practice": "practice",
        "difficulty": "Normal",
        "requested_question_count": 5,
        "cbt": [
            {
                "question": "Question",
                "choices": ["A", "B", "C", "D"],
                "answer_index": 0,
                "explanation": "explanation",
            }
        ],
    }


class StreamlitV103Tests(IsolatedWorldStateTestCase):
    def setUp(self):
        super().setUp()
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def navigation(self):
        return [
            item
            for item in self.app.radio
            if item.label == "주요 메뉴"
        ][0]

    def test_recovery_recommendation_opens_challenge_with_context(self):
        state = world_state.default_world_state()
        world_state.record_completed_round(state, make_lesson(), {0: 2})
        session = world_state.start_recovery_session(state)
        item = world_state.recovery_session_items(state, session)[0]
        world_state.submit_recovery_answer(
            state,
            session["id"],
            item["id"],
            item["answer_index"],
        )
        world_state.complete_recovery_session(state, session["id"])
        self.app.session_state["world_data"] = state
        self.navigation().set_value("Recovery").run()

        connect = [
            item
            for item in self.app.button
            if item.label == "도전 학습으로 연결"
        ][0]
        connect.click().run()

        self.assertEqual(self.app.session_state["active_view"], "Challenge")
        mode = [
            item
            for item in self.app.radio
            if item.label == "도전 유형"
        ][0]
        topic = [
            item
            for item in self.app.text_input
            if item.label == "학습할 주제를 입력하세요."
        ][0]
        self.assertEqual(mode.value, "Nightmare")
        self.assertEqual(topic.value, "Python")

    def test_ai_recommendation_creates_planner_records(self):
        state = world_state.default_world_state()
        world_state.add_ai_history(
            state,
            "추천",
            "추천",
            "Python 학습을 진행하세요.",
            "Python",
        )
        self.app.session_state["world_data"] = state
        self.navigation().set_value("AI").run()

        connect = [
            item
            for item in self.app.button
            if item.label == "학습 계획 목표·일정으로 연결"
        ][0]
        connect.click().run()

        planner = self.app.session_state["world_data"]["planner"]
        self.assertEqual(self.app.session_state["active_view"], "Planner")
        self.assertEqual(len(planner["goals"]), 1)
        self.assertEqual(len(planner["schedule"]), 1)
        self.assertEqual(planner["schedule"][0]["topic"], "Python")

    def test_planner_learning_schedule_transfers_topic(self):
        state = world_state.default_world_state()
        world_state.add_schedule(
            state,
            "Python 학습",
            date.today().isoformat(),
            "Learning",
            "Python",
        )
        self.app.session_state["world_data"] = state
        self.navigation().set_value("Planner").run()

        move = [item for item in self.app.button if item.label == "이동"][0]
        move.click().run()

        self.assertEqual(self.app.session_state["active_view"], "Learning")
        topic = [
            item
            for item in self.app.text_input
            if item.label == "학습할 주제를 입력하세요."
        ][0]
        self.assertEqual(topic.value, "Python")

    def test_report_download_uses_integrated_report(self):
        state = world_state.default_world_state()
        world_state.record_completed_round(state, make_lesson(), {0: 0})
        self.app.session_state["world_data"] = state
        self.navigation().set_value("Analytics").run()

        self.assertTrue(
            any(
                item.label == "학습 리포트 다운로드"
                for item in self.app.get("download_button")
            )
        )
        markdown = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("## 나의 학습", markdown)
        self.assertIn("## 학습 분석", markdown)


if __name__ == "__main__":
    unittest.main()
