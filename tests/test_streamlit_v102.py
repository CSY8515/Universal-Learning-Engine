import unittest

from streamlit.testing.v1 import AppTest

import world_state


def make_lesson(answer_index=0):
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
                "answer_index": answer_index,
                "explanation": "explanation",
            }
        ],
    }


class StreamlitV102Tests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def navigation(self):
        return [item for item in self.app.radio if item.label == "Primary navigation"][0]

    def test_every_world_has_a_real_entry(self):
        for world in world_state.WORLD_NAMES:
            self.navigation().set_value(world).run()
            headers = [item.value for item in self.app.header]
            self.assertIn(world, headers)
            self.assertFalse(self.app.exception)

    def test_completed_round_flows_into_recovery_and_can_be_recovered(self):
        state = world_state.default_world_state()
        world_state.record_completed_round(state, make_lesson(), {0: 2})
        self.app.session_state["world_data"] = state
        self.navigation().set_value("Recovery").run()

        start = [
            item for item in self.app.button if item.label == "Recovery Session 시작"
        ][0]
        start.click().run()
        answer = [
            item for item in self.app.radio if item.label == "복습 답을 선택하세요."
        ][0]
        answer.set_value(0).run()
        confirm = [
            item for item in self.app.button if item.label == "복습 정답 확인"
        ][0]
        confirm.click().run()
        complete = [
            item for item in self.app.button if item.label == "Recovery Session 완료"
        ][0]
        complete.click().run()

        sessions = self.app.session_state["world_data"]["recovery_sessions"]
        self.assertEqual(sessions[-1]["status"], "completed")
        self.assertEqual(
            world_state.pending_recovery_items(self.app.session_state["world_data"]),
            [],
        )

    def test_direct_and_practice_inputs_save_to_library(self):
        self.app.session_state["lesson"] = make_lesson()
        self.app.session_state["lesson_origin"] = "Learning"
        self.app.run()
        direct = [
            item for item in self.app.text_area if item.label == "직접 작성해보세요."
        ][0]
        practice = [
            item for item in self.app.text_area if item.label == "실습 답안을 작성해보세요."
        ][0]
        direct.set_value("직접 작성 결과").run()
        practice = [
            item for item in self.app.text_area if item.label == "실습 답안을 작성해보세요."
        ][0]
        practice.set_value("실습 결과").run()
        save = [
            item for item in self.app.button if item.label == "작성 내용 저장"
        ][0]
        save.click().run()

        notes = self.app.session_state["world_data"]["library"]["notes"]
        self.assertEqual(len(notes), 1)
        self.assertIn("직접 작성 결과", notes[0]["content"])
        self.assertIn("실습 결과", notes[0]["content"])

    def test_planner_goal_is_persisted_in_world_state(self):
        self.navigation().set_value("Planner").run()
        goal = [item for item in self.app.text_input if item.label == "새 목표"][0]
        goal.set_value("Python 복습 완료").run()
        add = [item for item in self.app.button if item.label == "목표 추가"][0]
        add.click().run()

        goals = self.app.session_state["world_data"]["planner"]["goals"]
        self.assertEqual(goals[-1]["title"], "Python 복습 완료")


if __name__ == "__main__":
    unittest.main()
