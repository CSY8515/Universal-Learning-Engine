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


class StreamlitV10Tests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def navigation(self):
        return [item for item in self.app.radio if item.label == "Primary navigation"][0]

    def test_dashboard_is_the_home_screen(self):
        headers = [item.value for item in self.app.header]
        self.assertIn("Dashboard", headers)
        self.assertEqual(self.app.session_state["active_view"], "Dashboard")
        self.assertEqual(
            self.navigation().options,
            ["Dashboard", "Learning", "Review"],
        )

    def test_injected_active_lesson_preserves_v09_learning_flow(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.run()
        self.assertEqual(self.app.session_state["active_view"], "Learning")
        answer_controls = [item for item in self.app.radio if item.label == "답을 선택하세요."]
        self.assertEqual(len(answer_controls), 1)

    def test_explicit_dashboard_navigation_does_not_clear_lesson(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.run()
        self.navigation().set_value("Dashboard").run()
        self.assertEqual(self.app.session_state["active_view"], "Dashboard")
        self.assertEqual(self.app.session_state["lesson"]["topic"], "Python")
        headers = [item.value for item in self.app.header]
        self.assertIn("Dashboard", headers)

    def test_dashboard_uses_completed_session_evidence(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["answers"] = {0: 0}
        self.app.session_state["answer_confidence"] = {0: "high"}
        self.app.session_state["round_finished"] = True
        self.app.run()
        self.navigation().set_value("Dashboard").run()

        metrics = {item.label: item.value for item in self.app.metric}
        self.assertEqual(metrics["Accuracy"], "100%")
        self.assertEqual(metrics["Learning Progress"], "1")
        subheaders = [item.value for item in self.app.subheader]
        self.assertIn("Recommended Next Step", subheaders)
        self.assertIn("Recent Round", subheaders)
        self.assertIn("Weakness Summary", subheaders)
        self.assertIn("Recent Activity", subheaders)

    def test_review_has_a_controlled_empty_state(self):
        self.navigation().set_value("Review").run()
        headers = [item.value for item in self.app.header]
        subheaders = [item.value for item in self.app.subheader]
        self.assertIn("Review", headers)
        self.assertIn("Nothing to review yet", subheaders)
        self.assertFalse(self.app.exception)

    def test_invalid_pending_navigation_metadata_is_repaired(self):
        self.app.session_state["pending_view"] = "bad"
        self.app.session_state["navigation_explicit"] = "bad"
        self.app.run()
        self.assertEqual(self.app.session_state["active_view"], "Dashboard")
        self.assertIsNone(self.app.session_state["pending_view"])
        self.assertFalse(self.app.session_state["navigation_explicit"])


if __name__ == "__main__":
    unittest.main()
