import unittest

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


class WorldIntegrationV103Tests(unittest.TestCase):
    def setUp(self):
        self.state = world_state.default_world_state()

    def _complete_recovery(self):
        world_state.record_completed_round(
            self.state,
            make_lesson(),
            {0: 2, 1: 3},
            duration_seconds=120,
        )
        session = world_state.start_recovery_session(self.state)
        for item in world_state.recovery_session_items(self.state, session):
            world_state.submit_recovery_answer(
                self.state,
                session["id"],
                item["id"],
                item["answer_index"],
            )
        return world_state.complete_recovery_session(self.state, session["id"])

    def test_recovery_recommendation_drives_independent_challenge_result(self):
        recovery = self._complete_recovery()
        recommendations = world_state.pending_recovery_recommendations(self.state)

        self.assertEqual(recovery["status"], "completed")
        self.assertEqual(len(recommendations), 1)
        recommendation = world_state.accept_recovery_recommendation(
            self.state,
            recommendations[0]["id"],
        )
        difficulty = (
            recommendation["mode"]
            if recommendation["mode"] in ("Hard", "Nightmare")
            else "Normal"
        )
        session = world_state.start_challenge_session(
            self.state,
            recommendation["mode"],
            recommendation["topic"],
            difficulty,
            5,
            source_recovery_recommendation_id=recommendation["id"],
        )
        lesson = make_lesson(recommendation["topic"], difficulty)
        lesson["challenge_mode"] = recommendation["mode"]
        lesson["challenge_session_id"] = session["id"]
        lesson["source_recovery_recommendation_id"] = recommendation["id"]
        record = world_state.record_completed_round(
            self.state,
            lesson,
            {0: 0, 1: 1},
            origin="Challenge",
            duration_seconds=90,
        )

        results = world_state.challenge_history(self.state)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["round_id"], record["id"])
        self.assertEqual(results[0]["session_id"], session["id"])
        self.assertEqual(
            self.state["recovery_recommendations"][0]["status"],
            "completed",
        )

    def test_ai_recommendation_creates_real_planner_goal_and_schedule(self):
        item = world_state.add_ai_history(
            self.state,
            "추천",
            "다음 학습 추천",
            "Python 오답을 보완하세요.",
            "Python",
        )
        link = world_state.connect_ai_recommendation_to_planner(
            self.state,
            item["id"],
            "2026-07-29",
        )
        duplicate = world_state.connect_ai_recommendation_to_planner(
            self.state,
            item["id"],
            "2026-07-29",
        )

        self.assertEqual(link, duplicate)
        self.assertEqual(link["status"], "linked")
        self.assertEqual(len(self.state["planner"]["goals"]), 1)
        self.assertEqual(len(self.state["planner"]["schedule"]), 1)
        self.assertEqual(self.state["planner"]["schedule"][0]["world"], "Learning")
        self.assertEqual(self.state["planner"]["schedule"][0]["topic"], "Python")

    def test_library_collects_every_generated_world_source(self):
        self._complete_recovery()
        ai_item = world_state.add_ai_history(
            self.state,
            "추천",
            "추천",
            "다음 학습",
            "Python",
        )
        world_state.connect_ai_recommendation_to_planner(
            self.state,
            ai_item["id"],
            "2026-07-29",
        )
        sources = {
            item.get("source_world")
            for item in self.state["library"]["resources"]
        }

        self.assertTrue({"Learning", "Recovery", "AI", "Planner"} <= sources)
        self.assertEqual(self.state["management"]["subjects"], ["Python"])

    def test_integrated_analytics_my_learning_and_report(self):
        self._complete_recovery()
        ai_item = world_state.add_ai_history(
            self.state,
            "추천",
            "추천",
            "다음 학습",
            "Python",
        )
        world_state.connect_ai_recommendation_to_planner(
            self.state,
            ai_item["id"],
            "2026-07-29",
        )
        world_state.add_note(self.state, "Python 노트", "정리 내용", "Python")

        analytics = world_state.build_world_analytics(self.state)
        stats = world_state.learning_stats(self.state)
        report = world_state.build_report(self.state)

        self.assertEqual(analytics["learning_round_count"], 1)
        self.assertEqual(analytics["recovery_session_count"], 1)
        self.assertEqual(analytics["ai_count"], 1)
        self.assertGreater(stats["study_seconds"], 0)
        self.assertEqual(stats["world_records"]["AI"], 1)
        for section in (
            "## 학습",
            "## 회복 학습",
            "## 도전 학습",
            "## 학습 분석",
            "## 인공지능",
            "## 학습 계획",
            "## 학습 자료실",
            "## 관리",
            "## 나의 학습",
        ):
            self.assertIn(section, report)

    def test_v102_state_normalizes_into_v103_schema(self):
        legacy = {
            "version": 1,
            "rounds": [],
            "recovery_sessions": [],
            "planner": {"goals": [], "schedule": []},
            "library": {"resources": [], "notes": []},
            "management": {
                "subjects": [],
                "settings": {
                    "default_question_count": 5,
                    "default_difficulty": "Easy",
                },
            },
            "ai_history": [
                {
                    "kind": "추천",
                    "prompt": "추천",
                    "response": "응답",
                    "topic": "Python",
                    "created_at": "2026-07-29T00:00:00+00:00",
                }
            ],
            "activity": [],
        }
        normalized = world_state.normalize_world_state(legacy)

        self.assertEqual(normalized["version"], world_state.STATE_VERSION)
        self.assertIn("challenge", normalized)
        self.assertIn("recovery_recommendations", normalized)
        self.assertTrue(normalized["ai_history"][0]["id"])
        self.assertEqual(
            normalized["ai_history"][0]["planner_link"]["status"],
            "available",
        )

    def test_legacy_state_stats_include_challenge_count(self):
        legacy = {
            "version": 1,
            "rounds": [],
            "recovery_sessions": [],
            "planner": {"goals": [], "schedule": []},
            "library": {"resources": [], "notes": []},
            "management": {
                "subjects": [],
                "settings": {
                    "default_question_count": 5,
                    "default_difficulty": "Easy",
                },
            },
            "ai_history": [],
            "activity": [],
        }

        stats = world_state.learning_stats(legacy)

        self.assertEqual(stats["challenge_count"], 0)
        self.assertEqual(stats["world_records"]["Challenge"], 0)
        self.assertNotIn("challenge", legacy)


if __name__ == "__main__":
    unittest.main()
