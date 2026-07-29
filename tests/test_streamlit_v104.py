import json
import unittest

from streamlit.testing.v1 import AppTest

import app
from tests._streamlit_case import IsolatedWorldStateTestCase


class StreamlitV104Tests(IsolatedWorldStateTestCase):
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

    def test_ai_is_disabled_without_a_user_key_but_other_worlds_work(self):
        self.navigation().set_value("AI").run()

        execute = [
            item for item in self.app.button if item.label == "AI 질문 실행"
        ][0]
        self.assertTrue(execute.disabled)
        self.navigation().set_value("Library").run()
        self.assertIn("Library", [item.value for item in self.app.header])
        self.assertFalse(self.app.exception)

    def test_register_change_and_delete_key_stays_out_of_world_data(self):
        self.navigation().set_value("Management").run()
        key_input = [
            item
            for item in self.app.text_input
            if item.label == "OpenAI API Key"
        ][0]
        register = [
            item for item in self.app.button if item.label == "API 등록"
        ][0]
        key_input.set_value("test-user-session-key")
        register.click().run()

        self.assertEqual(
            self.app.session_state[app.BYOK_API_KEY_STATE],
            "test-user-session-key",
        )
        self.assertNotIn(
            "test-user-session-key",
            json.dumps(self.app.session_state["world_data"]),
        )

        key_input = [
            item
            for item in self.app.text_input
            if item.label == "OpenAI API Key"
        ][0]
        change = [
            item for item in self.app.button if item.label == "API 변경"
        ][0]
        key_input.set_value("test-user-changed-key")
        change.click().run()
        self.assertEqual(
            self.app.session_state[app.BYOK_API_KEY_STATE],
            "test-user-changed-key",
        )

        delete = [
            item for item in self.app.button if item.label == "API 삭제"
        ][0]
        delete.click().run()
        self.assertEqual(self.app.session_state[app.BYOK_API_KEY_STATE], "")
        self.assertNotIn(
            "test-user-changed-key",
            json.dumps(self.app.session_state["world_data"]),
        )

    def test_registered_key_enables_all_four_ai_actions(self):
        self.app.session_state[app.BYOK_API_KEY_STATE] = "test-user-session-key"
        self.app.session_state[app.BYOK_CONNECTION_STATE] = "registered"
        self.navigation().set_value("AI").run()

        ai_kind = [
            item for item in self.app.radio if item.label == "AI 기능"
        ][0]
        self.assertEqual(ai_kind.options, ["질문", "해설", "추천", "요약"])
        execute = [
            item for item in self.app.button if item.label == "AI 질문 실행"
        ][0]
        self.assertFalse(execute.disabled)


if __name__ == "__main__":
    unittest.main()
