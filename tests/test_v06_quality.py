import json
import sys
import types
import unittest
from unittest.mock import patch

import app


def make_lesson():
    return {
        "topic": "Python",
        "tutorial": "tutorial",
        "example": "example",
        "direct_task": "task",
        "practice": "practice",
        "cbt": [
            {
                "question": f"Question {index + 1}",
                "choices": ["A", "B", "C", "D"],
                "answer_index": index % 4,
                "explanation": "explanation",
            }
            for index in range(5)
        ],
    }


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class V06QualityTests(unittest.TestCase):
    def test_parser_rejects_multiple_top_level_objects(self):
        with self.assertRaises(app.ResponseFormatError):
            app.parse_json_response('{"first": 1}\n{"second": 2}')

    def test_parser_rejects_non_object_and_accepts_braces_in_strings(self):
        with self.assertRaises(app.ResponseFormatError):
            app.parse_json_response('[1, 2, 3]')

        lesson = make_lesson()
        lesson["tutorial"] = "Use { and } as literal characters."
        wrapped = f"Generated lesson:\n{json.dumps(lesson)}\nEnd."
        self.assertEqual(app.parse_json_response(wrapped)["tutorial"], lesson["tutorial"])

    def test_empty_provider_text_is_controlled(self):
        response = types.SimpleNamespace(output_text="   ")
        with self.assertRaises(app.ResponseFormatError):
            app.extract_text(response)

    def test_boolean_indices_are_rejected_by_validation_and_scoring(self):
        lesson = make_lesson()
        lesson["cbt"][0]["answer_index"] = True
        with self.assertRaises(app.ResponseValidationError):
            app.validate_lesson(lesson, 5)

        self.assertFalse(app.is_correct_answer(True, 1))
        self.assertFalse(app.is_correct_answer(1, True))

    def test_duplicate_choices_use_unicode_case_and_whitespace_identity(self):
        lesson = make_lesson()
        lesson["cbt"][0]["choices"] = ["Ａ", " a ", "B", "C"]
        with self.assertRaises(app.ResponseValidationError):
            app.validate_lesson(lesson, 5)

    def test_transient_status_codes_are_retryable(self):
        self.assertTrue(app.should_try_api_fallback(ApiError("upstream", 500)))
        self.assertTrue(app.should_try_api_fallback(ApiError("upstream", 503)))
        self.assertFalse(app.should_try_api_fallback(ApiError("secret-value", 401)))
        self.assertFalse(app.should_try_api_fallback(ApiError("billing limit", 503)))

    def test_user_error_messages_do_not_expose_unknown_exception_text(self):
        message = app.user_facing_error_message(RuntimeError("secret-value"))
        self.assertNotIn("secret-value", message)
        self.assertIn("오류", message)

        provider_message = app.build_api_error_message()
        self.assertNotIn("secret-value", provider_message)

    def test_api_policy_has_explicit_timeout_and_one_fallback(self):
        calls = {"primary": 0, "fallback": 0, "client_kwargs": None}
        lesson_text = json.dumps(make_lesson())

        class Responses:
            def create(self, **_kwargs):
                calls["primary"] += 1
                raise ApiError("temporary outage", 503)

        class Completions:
            def create(self, **_kwargs):
                calls["fallback"] += 1
                return types.SimpleNamespace(
                    choices=[
                        types.SimpleNamespace(
                            message=types.SimpleNamespace(content=lesson_text)
                        )
                    ]
                )

        class FakeOpenAI:
            def __init__(self, **kwargs):
                calls["client_kwargs"] = kwargs
                self.responses = Responses()
                self.chat = types.SimpleNamespace(completions=Completions())

        fake_openai = types.SimpleNamespace(OpenAI=FakeOpenAI)
        with patch.dict(sys.modules, {"openai": fake_openai}), patch.object(
            app, "get_api_key", return_value="configured-key"
        ):
            result = app.generate_lesson("Python", 5, "Normal")

        self.assertEqual(calls["primary"], 1)
        self.assertEqual(calls["fallback"], 1)
        self.assertEqual(calls["client_kwargs"]["timeout"], app.API_TIMEOUT_SECONDS)
        self.assertEqual(calls["client_kwargs"]["max_retries"], 0)
        self.assertEqual(result["difficulty"], "Normal")

    def test_non_retryable_api_error_never_calls_fallback(self):
        calls = {"fallback": 0}

        class Responses:
            def create(self, **_kwargs):
                raise ApiError("private-provider-detail", 401)

        class Completions:
            def create(self, **_kwargs):
                calls["fallback"] += 1

        class FakeOpenAI:
            def __init__(self, **_kwargs):
                self.responses = Responses()
                self.chat = types.SimpleNamespace(completions=Completions())

        fake_openai = types.SimpleNamespace(OpenAI=FakeOpenAI)
        with patch.dict(sys.modules, {"openai": fake_openai}), patch.object(
            app, "get_api_key", return_value="configured-key"
        ):
            with self.assertRaises(app.ApiRequestError) as raised:
                app.generate_lesson("Python", 5, "Normal")

        self.assertEqual(calls["fallback"], 0)
        self.assertNotIn("private-provider-detail", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
