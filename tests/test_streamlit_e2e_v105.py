import json
import sys
import types
import unittest
from datetime import date
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import app
import world_state
from tests._streamlit_case import IsolatedWorldStateTestCase


def generated_lesson(question_count=5):
    return {
        "topic": "Python",
        "tutorial": "Python 핵심 개념",
        "example": "Python 적용 예제",
        "direct_task": "직접 작성 과제",
        "practice": "실습 과제",
        "cbt": [
            {
                "question": f"문제 {index + 1}",
                "choices": [
                    f"A{index}",
                    f"B{index}",
                    f"C{index}",
                    f"D{index}",
                ],
                "answer_index": 0,
                "explanation": "A가 정답입니다.",
            }
            for index in range(question_count)
        ],
    }


class SuccessfulOpenAI:
    lesson_json = json.dumps(generated_lesson(), ensure_ascii=False)

    class Responses:
        def create(self, **kwargs):
            prompt = str(kwargs.get("input", ""))
            if kwargs.get("max_output_tokens") == 8:
                return types.SimpleNamespace(output_text="OK")
            if '"tutorial"' in prompt and '"cbt"' in prompt:
                return types.SimpleNamespace(
                    output_text=SuccessfulOpenAI.lesson_json
                )
            return types.SimpleNamespace(output_text="검증된 AI 응답")

    def __init__(self, **_kwargs):
        self.responses = self.Responses()


class FailingOpenAI:
    class Responses:
        def create(self, **_kwargs):
            raise RuntimeError("private-provider-payload test-user-secret")

    def __init__(self, **_kwargs):
        self.responses = self.Responses()


class StreamlitEndToEndV105Tests(IsolatedWorldStateTestCase):
    def setUp(self):
        super().setUp()
        self.app = AppTest.from_file("app.py").run()
        self.assertFalse(self.app.exception)

    def navigation(self):
        return [
            item
            for item in self.app.radio
            if item.label == "Primary navigation"
        ][0]

    def button(self, label, *, key=None):
        matches = [
            item
            for item in self.app.button
            if item.label == label and (key is None or item.key == key)
        ]
        self.assertEqual(
            len(matches),
            1,
            f"Expected one button {label!r} with key {key!r}",
        )
        return matches[0]

    def enable_byok(self):
        self.app.session_state[app.BYOK_API_KEY_STATE] = "test-user-session-key"
        self.app.session_state[app.BYOK_CONNECTION_STATE] = "registered"

    def test_learning_and_challenge_start_buttons_use_the_registered_key(self):
        self.enable_byok()
        self.navigation().set_value("Learning").run()
        topic = [
            item
            for item in self.app.text_input
            if item.label == "학습할 주제를 입력하세요."
        ][0]
        topic.set_value("Python").run()
        with patch.dict(
            sys.modules,
            {"openai": types.SimpleNamespace(OpenAI=SuccessfulOpenAI)},
        ):
            self.button("학습 시작").click().run()

        self.assertEqual(self.app.session_state["lesson"]["topic"], "Python")
        self.assertEqual(self.app.session_state["lesson_origin"], "Learning")

        self.navigation().set_value("Challenge").run()
        mode = [
            item for item in self.app.radio if item.label == "Challenge 유형"
        ][0]
        mode.set_value("Hard").run()
        challenge_topic = [
            item
            for item in self.app.text_input
            if item.label == "학습할 주제를 입력하세요."
        ][0]
        challenge_topic.set_value("Python").run()
        with patch.dict(
            sys.modules,
            {"openai": types.SimpleNamespace(OpenAI=SuccessfulOpenAI)},
        ):
            self.button("학습 시작").click().run()

        self.assertEqual(self.app.session_state["lesson_origin"], "Challenge")
        self.assertEqual(
            self.app.session_state["lesson"]["challenge_mode"],
            "Hard",
        )
        self.assertEqual(
            len(
                self.app.session_state["world_data"]["challenge"]["sessions"]
            ),
            1,
        )

    def test_api_connection_and_all_ai_buttons_feed_the_learning_flow(self):
        self.enable_byok()
        self.navigation().set_value("Management").run()
        with patch.dict(
            sys.modules,
            {"openai": types.SimpleNamespace(OpenAI=SuccessfulOpenAI)},
        ):
            self.button("연결 테스트").click().run()
        self.assertEqual(
            self.app.session_state[app.BYOK_CONNECTION_STATE],
            "connected",
        )

        self.navigation().set_value("AI").run()
        for kind in ("질문", "해설", "요약", "추천"):
            selector = [
                item for item in self.app.radio if item.label == "AI 기능"
            ][0]
            selector.set_value(kind).run()
            request = [
                item
                for item in self.app.text_area
                if item.label == f"AI {kind}"
            ][0]
            request.set_value(f"{kind}을 검증해주세요.").run()
            with patch.dict(
                sys.modules,
                {"openai": types.SimpleNamespace(OpenAI=SuccessfulOpenAI)},
            ):
                self.button(f"AI {kind} 실행").click().run()

        state = self.app.session_state["world_data"]
        self.assertEqual(
            [item["kind"] for item in state["ai_history"]],
            ["질문", "해설", "요약", "추천"],
        )
        self.assertEqual(
            len(
                [
                    item
                    for item in state["library"]["resources"]
                    if item.get("source_world") == "AI"
                ]
            ),
            4,
        )

        latest_id = state["ai_history"][-1]["id"]
        self.button(
            "Planner 목표·일정으로 연결",
            key=f"connect_ai_planner_{latest_id}",
        ).click().run()
        planner = self.app.session_state["world_data"]["planner"]
        self.assertEqual(self.app.session_state["active_view"], "Planner")
        self.assertEqual(len(planner["goals"]), 1)
        self.assertEqual(len(planner["schedule"]), 1)

    def test_planner_library_and_management_buttons_persist_updates(self):
        self.navigation().set_value("Planner").run()
        goal_input = [
            item for item in self.app.text_input if item.label == "새 목표"
        ][0]
        goal_input.set_value("Python 목표").run()
        self.button("목표 추가").click().run()
        state = self.app.session_state["world_data"]
        goal_id = state["planner"]["goals"][-1]["id"]
        self.button("완료", key=f"toggle_goal_{goal_id}").click().run()
        self.assertTrue(
            self.app.session_state["world_data"]["planner"]["goals"][-1][
                "completed"
            ]
        )
        self.button("다시 열기", key=f"toggle_goal_{goal_id}").click().run()
        self.assertFalse(
            self.app.session_state["world_data"]["planner"]["goals"][-1][
                "completed"
            ]
        )

        schedule_title = [
            item
            for item in self.app.text_input
            if item.label == "일정 제목"
        ][0]
        schedule_topic = [
            item
            for item in self.app.text_input
            if item.label == "연결 주제 (선택)"
        ][0]
        schedule_title.set_value("Python 학습").run()
        schedule_topic = [
            item
            for item in self.app.text_input
            if item.label == "연결 주제 (선택)"
        ][0]
        schedule_topic.set_value("Python").run()
        self.button("일정 추가").click().run()
        schedule = self.app.session_state["world_data"]["planner"]["schedule"][-1]
        self.assertEqual(
            schedule["scheduled_date"],
            date.today().isoformat(),
        )

        self.button("이동", key=f"open_schedule_{schedule['id']}").click().run()
        self.assertEqual(self.app.session_state["active_view"], "Learning")
        self.assertEqual(self.app.session_state["learning_topic_input"], "Python")
        self.navigation().set_value("Planner").run()
        self.button(
            "완료",
            key=f"complete_schedule_{schedule['id']}",
        ).click().run()
        self.assertTrue(
            self.app.session_state["world_data"]["planner"]["schedule"][-1][
                "completed"
            ]
        )

        self.navigation().set_value("Library").run()
        for label, value in (
            ("노트 제목", "Python 노트"),
            ("노트 주제", "Python"),
        ):
            field = [
                item for item in self.app.text_input if item.label == label
            ][0]
            field.set_value(value).run()
        content = [
            item for item in self.app.text_area if item.label == "노트 내용"
        ][0]
        content.set_value("Python 정리 내용").run()
        self.button("노트 저장").click().run()
        self.assertEqual(
            self.app.session_state["world_data"]["library"]["notes"][-1][
                "title"
            ],
            "Python 노트",
        )
        search = [
            item
            for item in self.app.text_input
            if item.label == "자료와 노트 검색"
        ][0]
        search.set_value("Python 정리").run()
        self.assertIn(
            "검색 결과 1개",
            [item.value for item in self.app.subheader],
        )

        self.navigation().set_value("Management").run()
        subject = [
            item for item in self.app.text_input if item.label == "과목 추가"
        ][0]
        subject.set_value("Python").run()
        self.button("과목 저장").click().run()
        self.assertIn(
            "Python",
            self.app.session_state["world_data"]["management"]["subjects"],
        )
        self.button("선택 과목 제거").click().run()
        self.assertNotIn(
            "Python",
            self.app.session_state["world_data"]["management"]["subjects"],
        )

        count_setting = [
            item
            for item in self.app.selectbox
            if item.label == "기본 문제 수"
        ][0]
        difficulty_setting = [
            item
            for item in self.app.selectbox
            if item.label == "기본 난이도"
        ][0]
        count_setting.set_value(10).run()
        difficulty_setting = [
            item
            for item in self.app.selectbox
            if item.label == "기본 난이도"
        ][0]
        difficulty_setting.set_value("Hard").run()
        self.button("설정 저장").click().run()
        settings = self.app.session_state["world_data"]["management"]["settings"]
        self.assertEqual(settings["default_question_count"], 10)
        self.assertEqual(settings["default_difficulty"], "Hard")

        self.assertTrue(
            any(
                item.label == "백업 다운로드"
                for item in self.app.get("download_button")
            )
        )
        self.button("백업 복원").click().run()
        self.assertTrue(
            any(
                "복원할 백업 파일" in item.value
                for item in self.app.warning
            )
        )

    def test_no_key_navigation_and_provider_failure_are_isolated(self):
        self.navigation().set_value("AI").run()
        self.button("API 설정으로 이동").click().run()
        self.assertEqual(self.app.session_state["active_view"], "Management")

        self.enable_byok()
        self.navigation().set_value("AI").run()
        request = [
            item for item in self.app.text_area if item.label == "AI 질문"
        ][0]
        request.set_value("오류 격리 검증").run()
        with patch.dict(
            sys.modules,
            {"openai": types.SimpleNamespace(OpenAI=FailingOpenAI)},
        ):
            self.button("AI 질문 실행").click().run()

        rendered_errors = "\n".join(item.value for item in self.app.error)
        self.assertNotIn("private-provider-payload", rendered_errors)
        self.assertNotIn("test-user-secret", rendered_errors)
        self.navigation().set_value("Library").run()
        self.assertFalse(self.app.exception)

    def test_all_worlds_hide_internal_and_legacy_markers(self):
        state = world_state.default_world_state()
        world_state.add_note(
            state,
            "사용자 노트",
            "정상 사용자 콘텐츠",
            "Python",
        )
        self.app.session_state["world_data"] = state
        self.app.session_state[app.BYOK_API_KEY_STATE] = "private-session-marker"

        forbidden = (
            "traceback",
            "debug",
            "internal data",
            "legacy",
            "dummy",
            "placeholder",
            "private-session-marker",
        )
        rendered = []
        for world in world_state.WORLD_NAMES:
            self.navigation().set_value(world).run()
            self.assertFalse(self.app.exception)
            for element_type in (
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
                    str(item.value)
                    for item in self.app.get(element_type)
                )

        visible_text = "\n".join(rendered).casefold()
        for marker in forbidden:
            self.assertNotIn(marker, visible_text)


if __name__ == "__main__":
    unittest.main()
