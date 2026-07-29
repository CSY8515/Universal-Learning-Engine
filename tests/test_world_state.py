import tempfile
import unittest
from pathlib import Path

import world_state


def make_lesson():
    return {
        "topic": "Python",
        "tutorial": "기초 개념",
        "example": "예제",
        "direct_task": "직접 과제",
        "practice": "실습",
        "difficulty": "Normal",
        "cbt": [
            {
                "question": "정답은?",
                "choices": ["A", "B", "C", "D"],
                "answer_index": 0,
                "explanation": "A가 정답입니다.",
            },
            {
                "question": "두 번째 정답은?",
                "choices": ["A", "B", "C", "D"],
                "answer_index": 1,
                "explanation": "B가 정답입니다.",
            },
        ],
    }


class WorldStateTests(unittest.TestCase):
    def setUp(self):
        self.state = world_state.default_world_state()

    def test_completed_round_connects_recovery_library_and_management(self):
        record = world_state.record_completed_round(
            self.state,
            make_lesson(),
            {0: 0, 1: 3},
            duration_seconds=125,
        )
        duplicate = world_state.record_completed_round(
            self.state,
            make_lesson(),
            {0: 0, 1: 3},
            duration_seconds=125,
        )

        self.assertIs(record, duplicate)
        self.assertEqual(len(self.state["rounds"]), 1)
        self.assertEqual(record["wrong_count"], 1)
        self.assertEqual(len(world_state.pending_recovery_items(self.state)), 1)
        self.assertEqual(len(self.state["library"]["resources"]), 1)
        self.assertEqual(self.state["management"]["subjects"], ["Python"])

    def test_recovery_session_marks_only_correct_answers_recovered(self):
        world_state.record_completed_round(
            self.state, make_lesson(), {0: 2, 1: 3}
        )
        session = world_state.start_recovery_session(self.state)
        items = world_state.recovery_session_items(self.state, session)
        world_state.submit_recovery_answer(
            self.state, session["id"], items[0]["id"], items[0]["answer_index"]
        )
        wrong_selection = (items[1]["answer_index"] + 1) % 4
        world_state.submit_recovery_answer(
            self.state, session["id"], items[1]["id"], wrong_selection
        )
        completed = world_state.complete_recovery_session(self.state, session["id"])

        self.assertEqual(completed["correct_count"], 1)
        self.assertEqual(len(world_state.pending_recovery_items(self.state)), 1)

    def test_planner_goal_schedule_and_today_flow(self):
        goal = world_state.add_goal(self.state, "Python 완료", "2026-08-01")
        world_state.set_goal_completed(self.state, goal["id"], True)
        item = world_state.add_schedule(
            self.state, "오답 복습", "2026-07-28", "Recovery", "Python"
        )

        self.assertTrue(goal["completed"])
        self.assertEqual(
            world_state.today_schedule(self.state, "2026-07-28"),
            [item],
        )

    def test_library_note_and_search(self):
        world_state.add_note(self.state, "반복문", "for 문 정리", "Python")
        results = world_state.search_library(self.state, "for 문")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["kind"], "노트")

    def test_learning_stats_and_report(self):
        world_state.record_completed_round(
            self.state,
            make_lesson(),
            {0: 0, 1: 1},
            duration_seconds=180,
        )
        stats = world_state.learning_stats(self.state)
        report = world_state.build_report(self.state)

        self.assertEqual(stats["round_count"], 1)
        self.assertEqual(stats["study_seconds"], 180)
        self.assertEqual(stats["accuracy"], 100)
        self.assertIn("첫 학습 완료", stats["achievements"])
        self.assertIn("Python", report)

    def test_backup_round_trip_and_file_storage(self):
        world_state.add_goal(self.state, "백업 목표")
        encoded = world_state.export_world_state(self.state)
        restored = world_state.import_world_state(encoded)
        self.assertEqual(restored["planner"]["goals"][0]["title"], "백업 목표")

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "state.json"
            world_state.save_world_state(restored, target)
            loaded = world_state.load_world_state(target)
        self.assertEqual(loaded["planner"]["goals"][0]["title"], "백업 목표")


if __name__ == "__main__":
    unittest.main()
