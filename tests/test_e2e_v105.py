import tempfile
import unittest
from pathlib import Path

import world_state


def make_lesson(topic="Python", difficulty="Normal"):
    return {
        "topic": topic,
        "tutorial": "핵심 개념",
        "example": "적용 예제",
        "direct_task": "직접 과제",
        "practice": "실습",
        "difficulty": difficulty,
        "requested_question_count": 5,
        "cbt": [
            {
                "question": "첫 번째 문제",
                "choices": ["A", "B", "C", "D"],
                "answer_index": 0,
                "explanation": "A가 정답입니다.",
            },
            {
                "question": "두 번째 문제",
                "choices": ["A", "B", "C", "D"],
                "answer_index": 1,
                "explanation": "B가 정답입니다.",
            },
        ],
    }


class EndToEndV105Tests(unittest.TestCase):
    def test_complete_world_flow_uses_one_normalized_evidence_set(self):
        state = world_state.default_world_state()

        learning = world_state.record_completed_round(
            state,
            make_lesson(),
            {0: 2, 1: 3},
            duration_seconds=120,
        )
        recovery_session = world_state.start_recovery_session(state)
        for item in world_state.recovery_session_items(state, recovery_session):
            world_state.submit_recovery_answer(
                state,
                recovery_session["id"],
                item["id"],
                item["answer_index"],
            )
        recovery = world_state.complete_recovery_session(
            state,
            recovery_session["id"],
        )

        recommendation = world_state.accept_recovery_recommendation(
            state,
            world_state.pending_recovery_recommendations(state)[0]["id"],
        )
        challenge_difficulty = (
            recommendation["mode"]
            if recommendation["mode"] in ("Hard", "Nightmare")
            else "Normal"
        )
        challenge_session = world_state.start_challenge_session(
            state,
            recommendation["mode"],
            recommendation["topic"],
            challenge_difficulty,
            5,
            source_recovery_recommendation_id=recommendation["id"],
        )
        challenge_lesson = make_lesson(
            recommendation["topic"],
            challenge_difficulty,
        )
        challenge_lesson.update(
            {
                "challenge_mode": recommendation["mode"],
                "challenge_session_id": challenge_session["id"],
                "source_recovery_recommendation_id": recommendation["id"],
            }
        )
        challenge = world_state.record_completed_round(
            state,
            challenge_lesson,
            {0: 0, 1: 1},
            origin="Challenge",
            duration_seconds=90,
        )

        ai_records = [
            world_state.add_ai_history(
                state,
                kind,
                f"{kind} 요청",
                f"{kind} 결과",
                "Python",
            )
            for kind in ("질문", "해설", "요약", "추천")
        ]
        planner_link = world_state.connect_ai_recommendation_to_planner(
            state,
            ai_records[-1]["id"],
            "2026-07-30",
        )
        goal = world_state.set_goal_completed(
            state,
            planner_link["goal_id"],
            True,
        )
        schedule = world_state.set_schedule_completed(
            state,
            planner_link["schedule_id"],
            True,
        )
        note = world_state.add_note(
            state,
            "Python 통합 노트",
            "Learning부터 AI까지 정리",
            "Python",
        )

        analytics = world_state.build_world_analytics(state)
        stats = world_state.learning_stats(state)
        report = world_state.build_report(state)

        self.assertEqual(learning["origin"], "Learning")
        self.assertEqual(recovery["status"], "completed")
        self.assertEqual(challenge["origin"], "Challenge")
        self.assertEqual(analytics["learning_round_count"], 1)
        self.assertEqual(analytics["recovery_session_count"], 1)
        self.assertEqual(analytics["challenge_session_count"], 1)
        self.assertEqual(analytics["ai_count"], 4)
        self.assertTrue(goal["completed"])
        self.assertTrue(schedule["completed"])
        self.assertEqual(
            world_state.search_library(state, "통합 노트")[0]["id"],
            note["id"],
        )
        self.assertEqual(stats["world_records"]["AI"], 4)
        for section in (
            "## Learning",
            "## Recovery",
            "## Challenge",
            "## Analytics",
            "## AI",
            "## Planner",
            "## Library",
            "## Management",
            "## My Learning",
        ):
            self.assertIn(section, report)

    def test_supported_create_read_update_delete_and_backup_round_trip(self):
        state = world_state.default_world_state()

        goal = world_state.add_goal(state, "Python 완료", "2026-08-01")
        self.assertEqual(state["planner"]["goals"][0]["id"], goal["id"])
        world_state.set_goal_completed(state, goal["id"], True)
        self.assertTrue(state["planner"]["goals"][0]["completed"])
        world_state.set_goal_completed(state, goal["id"], False)
        self.assertFalse(state["planner"]["goals"][0]["completed"])

        schedule = world_state.add_schedule(
            state,
            "Python 학습",
            "2026-07-30",
            "Learning",
            "Python",
        )
        world_state.set_schedule_completed(state, schedule["id"], True)
        self.assertTrue(state["planner"]["schedule"][0]["completed"])

        note = world_state.add_note(
            state,
            "반복문",
            "for 문 정리",
            "Python",
        )
        self.assertEqual(world_state.search_library(state, "for 문")[0]["id"], note["id"])

        subjects = state["management"]["subjects"]
        subjects.append("SQL")
        self.assertIn("SQL", subjects)
        subjects.remove("SQL")
        self.assertNotIn("SQL", subjects)

        settings = state["management"]["settings"]
        settings["default_question_count"] = 10
        settings["default_difficulty"] = "Hard"
        normalized = world_state.normalize_world_state(state)
        self.assertEqual(normalized["management"]["settings"]["default_question_count"], 10)
        self.assertEqual(normalized["management"]["settings"]["default_difficulty"], "Hard")

        encoded = world_state.export_world_state(normalized)
        restored = world_state.import_world_state(encoded)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "world-state.json"
            world_state.save_world_state(restored, target)
            loaded = world_state.load_world_state(target)

        self.assertEqual(loaded, restored)
        self.assertNotIn("user_openai_api_key", encoded)
        self.assertNotIn("openai_connection_status", encoded)


if __name__ == "__main__":
    unittest.main()
