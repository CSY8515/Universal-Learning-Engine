import sys
import types
import unittest
from unittest.mock import patch

import app
import world_state


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ByokV104Tests(unittest.TestCase):
    def test_api_key_normalization_rejects_empty_whitespace_and_oversize_values(self):
        self.assertEqual(
            app.normalize_api_key_input("  test-user-key  "),
            "test-user-key",
        )
        self.assertEqual(app.normalize_api_key_input(""), "")
        self.assertEqual(app.normalize_api_key_input("test-user key"), "")
        self.assertEqual(app.normalize_api_key_input("x" * 513), "")
        self.assertEqual(app.normalize_api_key_input(None), "")

    def test_connection_test_uses_only_the_supplied_key(self):
        calls = {"client": None, "request": None}

        class Responses:
            def create(self, **kwargs):
                calls["request"] = kwargs
                return types.SimpleNamespace(output_text="OK")

        class FakeOpenAI:
            def __init__(self, **kwargs):
                calls["client"] = kwargs
                self.responses = Responses()

        with patch.dict(
            sys.modules,
            {"openai": types.SimpleNamespace(OpenAI=FakeOpenAI)},
        ):
            self.assertTrue(app.test_openai_connection("test-user-key"))

        self.assertEqual(calls["client"]["api_key"], "test-user-key")
        self.assertEqual(calls["client"]["max_retries"], 0)
        self.assertEqual(calls["request"]["max_output_tokens"], 8)

    def test_connection_failure_does_not_expose_provider_or_key_text(self):
        class Responses:
            def create(self, **_kwargs):
                raise ApiError("test-user-secret invalid", 401)

        class FakeOpenAI:
            def __init__(self, **_kwargs):
                self.responses = Responses()

        with patch.dict(
            sys.modules,
            {"openai": types.SimpleNamespace(OpenAI=FakeOpenAI)},
        ):
            with self.assertRaises(app.ApiRequestError) as raised:
                app.test_openai_connection("test-user-secret")

        self.assertNotIn("test-user-secret", str(raised.exception))
        self.assertNotIn("invalid", str(raised.exception).lower())

    def test_ai_explanation_uses_responses_api(self):
        calls = {"prompt": ""}

        class Responses:
            def create(self, **kwargs):
                calls["prompt"] = kwargs["input"]
                return types.SimpleNamespace(output_text="단계별 해설")

        class FakeOpenAI:
            def __init__(self, **_kwargs):
                self.responses = Responses()

        with (
            patch.dict(
                sys.modules,
                {"openai": types.SimpleNamespace(OpenAI=FakeOpenAI)},
            ),
            patch.object(app, "get_api_key", return_value="test-user-key"),
            patch.object(app, "_ai_context", return_value="학습 기록"),
        ):
            result = app.generate_ai_world_text("해설", "오답을 설명해주세요.")

        self.assertEqual(result, "단계별 해설")
        self.assertIn("단계적으로", calls["prompt"])
        self.assertIn("오답을 설명해주세요.", calls["prompt"])

    def test_ai_explanation_flows_to_library_without_api_key_data(self):
        state = world_state.default_world_state()
        world_state.add_ai_history(
            state,
            "해설",
            "오답을 설명해주세요.",
            "단계별 해설",
            "Python",
        )

        exported = world_state.export_world_state(state)

        self.assertEqual(state["ai_history"][-1]["kind"], "해설")
        self.assertEqual(state["library"]["resources"][-1]["source_world"], "AI")
        self.assertNotIn("test-user-key", exported)


if __name__ == "__main__":
    unittest.main()
