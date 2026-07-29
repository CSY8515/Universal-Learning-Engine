import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

import app
import world_state
from tests._streamlit_case import IsolatedWorldStateTestCase


def make_lesson(topic="파이썬", difficulty="Normal"):
    return {
        "topic": topic,
        "tutorial": "핵심 개념",
        "example": "적용 예제",
        "direct_task": "직접 과제",
        "practice": "실습 과제",
        "difficulty": difficulty,
        "requested_question_count": 5,
        "cbt": [
            {
                "question": "첫 번째 문제",
                "choices": ["가", "나", "다", "라"],
                "answer_index": 0,
                "explanation": "가가 정답입니다.",
            }
        ],
    }


class UserDataManagementV106Tests(IsolatedWorldStateTestCase):
    def populated_state(self):
        state = world_state.default_world_state()
        learning = world_state.record_completed_round(
            state,
            make_lesson(),
            {0: 2},
        )
        recovery = world_state.start_recovery_session(state)
        ai_record = world_state.add_ai_history(
            state,
            "추천",
            "다음 학습을 추천해주세요.",
            "파이썬 기초를 복습하세요.",
            "파이썬",
        )
        planner = world_state.connect_ai_recommendation_to_planner(
            state,
            ai_record["id"],
            "2026-07-30",
        )
        note = world_state.add_note(
            state,
            "파이썬 노트",
            "반복문 정리",
            "파이썬",
        )
        return state, learning, recovery, ai_record, planner, note

    def test_selected_learning_record_deletes_connected_generated_data(self):
        state, learning, recovery, _ai, _planner, note = self.populated_state()
        deleted = world_state.delete_selected_records(
            state,
            [f"round:{learning['id']}"],
        )

        self.assertEqual(deleted, 1)
        self.assertFalse(state["rounds"])
        self.assertNotIn(
            recovery["id"],
            [item["id"] for item in state["recovery_sessions"]],
        )
        self.assertFalse(
            any(
                item.get("source_id") == learning["id"]
                for item in state["library"]["resources"]
            )
        )
        self.assertIn(note["id"], [item["id"] for item in state["library"]["notes"]])

    def test_selected_ai_record_deletes_planner_links_and_generated_resource(self):
        state, _learning, _recovery, ai_record, planner, _note = (
            self.populated_state()
        )
        deleted = world_state.delete_selected_records(
            state,
            [f"ai:{ai_record['id']}"],
        )

        self.assertEqual(deleted, 1)
        self.assertFalse(state["ai_history"])
        self.assertNotIn(
            planner["goal_id"],
            [item["id"] for item in state["planner"]["goals"]],
        )
        self.assertNotIn(
            planner["schedule_id"],
            [item["id"] for item in state["planner"]["schedule"]],
        )
        self.assertFalse(
            any(
                item.get("source_id") == ai_record["id"]
                for item in state["library"]["resources"]
            )
        )

    def test_clear_all_records_preserves_subjects_and_settings(self):
        state, *_items = self.populated_state()
        state["management"]["subjects"].append("수학")
        state["management"]["settings"]["default_question_count"] = 10
        state["management"]["settings"]["default_difficulty"] = "Hard"

        deleted = world_state.clear_all_records(state)

        self.assertGreater(deleted, 0)
        self.assertEqual(state["rounds"], [])
        self.assertEqual(state["planner"]["goals"], [])
        self.assertEqual(state["library"]["notes"], [])
        self.assertIn("수학", state["management"]["subjects"])
        self.assertEqual(
            state["management"]["settings"]["default_question_count"],
            10,
        )
        self.assertEqual(
            state["management"]["settings"]["default_difficulty"],
            "Hard",
        )

    def test_reset_user_data_restores_defaults_without_old_records(self):
        state, *_items = self.populated_state()
        deleted = world_state.reset_user_data(state)

        self.assertGreater(deleted, 0)
        self.assertEqual(state, world_state.default_world_state())

    def test_legacy_system_titles_are_localized_in_deletion_catalog(self):
        state = world_state.default_world_state()
        goal = world_state.add_goal(state, "AI 추천 학습", "2026-07-30")
        resource = world_state.add_note(
            state,
            "사용자 작성 AI 노트",
            "사용자 내용은 보존합니다.",
            "",
        )
        state["library"]["resources"].append(
            {
                "id": "old-resource",
                "source_world": "Recovery",
                "source_id": "old-source",
                "kind": "Recovery Record",
                "title": "Python Recovery Session",
                "topic": "",
                "content": "",
                "details": {},
                "created_at": "2026-07-29T00:00:00+00:00",
            }
        )

        labels = {
            item["token"]: item["label"]
            for item in world_state.deletion_catalog(state)
        }
        self.assertIn("인공지능 추천 학습", labels[f"goal:{goal['id']}"])
        self.assertIn("회복 학습", labels["resource:old-resource"])
        self.assertNotIn("Recovery Session", labels["resource:old-resource"])
        self.assertIn("AI", labels[f"note:{resource['id']}"])

    def test_streamlit_developer_chrome_is_hidden(self):
        css = (
            Path(__file__).resolve().parent.parent / "assets" / "ule.css"
        ).read_text(encoding="utf-8")
        self.assertIn('[data-testid="stAppDeployButton"]', css)
        self.assertIn('[data-testid="stMainMenu"]', css)
        self.assertIn("display: none !important", css)


class StreamlitLocalizationV106Tests(IsolatedWorldStateTestCase):
    def setUp(self):
        super().setUp()
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def navigation(self):
        return [item for item in self.app.radio if item.label == "주요 메뉴"][0]

    def visible_text(self):
        rendered = []
        for element_type in (
            "title",
            "header",
            "subheader",
            "markdown",
            "text",
            "caption",
            "info",
            "warning",
            "error",
            "success",
        ):
            rendered.extend(
                str(item.value) for item in self.app.get(element_type)
            )
        for element_type in (
            "button",
            "checkbox",
            "text_input",
            "text_area",
            "selectbox",
            "radio",
            "multiselect",
            "file_uploader",
            "download_button",
        ):
            for item in self.app.get(element_type):
                rendered.append(str(getattr(item, "label", "")))
                rendered.extend(str(value) for value in getattr(item, "options", []))
        return "\n".join(rendered)

    def test_all_worlds_use_korean_labels_and_hide_developer_markers(self):
        expected_headers = {
            "Learning": "학습",
            "Recovery": "회복 학습",
            "Challenge": "도전 학습",
            "Analytics": "학습 분석",
            "AI": "인공지능",
            "Planner": "학습 계획",
            "Library": "학습 자료실",
            "Management": "관리",
            "My Learning": "나의 학습",
        }
        forbidden = re.compile(
            r"\b(?:JSON|Debug|Internal|Legacy|Dummy|Placeholder|TODO|"
            r"Learning|Recovery|Challenge|Analytics|Planner|Library|"
            r"Management|Report|OpenAI|API|CBT)\b",
            re.IGNORECASE,
        )

        for world, heading in expected_headers.items():
            self.navigation().set_value(world).run()
            self.assertFalse(self.app.exception)
            self.assertIn(heading, [item.value for item in self.app.header])
            self.assertIsNone(
                forbidden.search(self.visible_text()),
                f"{world} 화면에 개발자용 또는 영문 문구가 노출되었습니다.",
            )

    def test_byok_delete_requires_explicit_confirmation(self):
        self.app.session_state[app.BYOK_API_KEY_STATE] = "session-test-key"
        self.navigation().set_value("Management").run()
        delete = [
            item for item in self.app.button if item.label == "연결 키 삭제"
        ][0]
        self.assertTrue(delete.disabled)

        confirm = [
            item
            for item in self.app.checkbox
            if item.label == "연결 키 삭제에 동의합니다."
        ][0]
        confirm.check().run()
        delete = [
            item for item in self.app.button if item.label == "연결 키 삭제"
        ][0]
        self.assertFalse(delete.disabled)

    def test_destructive_data_actions_are_disabled_without_confirmation(self):
        state = world_state.default_world_state()
        world_state.record_completed_round(state, make_lesson(), {0: 0})
        self.app.session_state["world_data"] = state
        self.navigation().set_value("Management").run()

        selected_delete = [
            item
            for item in self.app.button
            if item.label == "선택한 기록 삭제"
        ][0]
        category_delete = [
            item
            for item in self.app.button
            if item.label == "이 종류의 기록 모두 삭제"
        ][0]
        all_delete = [
            item
            for item in self.app.button
            if item.label == "모든 학습 기록 삭제"
        ][0]
        reset = [
            item
            for item in self.app.button
            if item.label == "모든 사용자 데이터 초기화"
        ][0]
        self.assertTrue(selected_delete.disabled)
        self.assertTrue(category_delete.disabled)
        self.assertTrue(all_delete.disabled)
        self.assertTrue(reset.disabled)
