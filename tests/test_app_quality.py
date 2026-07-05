import json
import unittest

import app


def make_lesson(count=5):
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
            for index in range(count)
        ],
    }


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class AppQualityTests(unittest.TestCase):
    def test_parse_json_plain_codeblock_and_wrapped_text(self):
        data = make_lesson()
        raw_json = json.dumps(data)

        self.assertEqual(app.parse_json_response(raw_json)["topic"], "Python")
        self.assertEqual(app.parse_json_response(f"```json\n{raw_json}\n```")["topic"], "Python")
        self.assertEqual(app.parse_json_response(f"Here is JSON:\n{raw_json}\nDone.")["topic"], "Python")

    def test_validate_lesson_question_count(self):
        lesson = make_lesson(7)

        app.validate_lesson(lesson, 5)

        self.assertEqual(len(lesson["cbt"]), 5)
        self.assertIn("cbt_count_notice", lesson)

    def test_validate_lesson_rejects_bad_answer_index(self):
        lesson = make_lesson()
        lesson["cbt"][0]["answer_index"] = 4

        with self.assertRaises(ValueError):
            app.validate_lesson(lesson, 5)

    def test_validate_lesson_rejects_duplicate_choices(self):
        lesson = make_lesson()
        lesson["cbt"][0]["choices"] = ["A", "A", "B", "C"]

        with self.assertRaises(ValueError):
            app.validate_lesson(lesson, 5)

    def test_cbt_scoring_uses_index_not_choice_text(self):
        choices = ["A", "A", "B", "C"]
        answer_index = 1

        self.assertFalse(app.is_correct_answer(0, answer_index))
        self.assertTrue(app.is_correct_answer(1, answer_index))
        self.assertEqual(choices[0], choices[1])

    def test_api_fallback_conditions(self):
        self.assertFalse(app.should_try_api_fallback(ApiError("invalid api key", 401)))
        self.assertFalse(app.should_try_api_fallback(ApiError("insufficient_quota", 429)))
        self.assertFalse(app.should_try_api_fallback(ApiError("billing hard limit reached")))
        self.assertTrue(app.should_try_api_fallback(ApiError("Connection error")))
        self.assertTrue(app.should_try_api_fallback(ApiError("Request timeout")))

    def test_v03_difficulty_prompt_rules(self):
        self.assertEqual(app.DIFFICULTY_OPTIONS, ["Easy", "Normal", "Hard", "Nightmare"])

        hard_prompt = app.build_prompt("investment", 5, "Hard")
        nightmare_prompt = app.build_prompt("English", 5, "Nightmare")

        self.assertIn("application, comparison, and case-based reasoning", hard_prompt)
        self.assertIn("connect at least 2 concepts", hard_prompt)
        self.assertIn("plausible distractors", hard_prompt)
        self.assertIn("complex scenario", nightmare_prompt)
        self.assertIn("multi-step reasoning", nightmare_prompt)
        self.assertIn("trap choices", nightmare_prompt)
        self.assertIn("connect at least 3 concepts", nightmare_prompt)
        self.assertIn("why the correct answer is best and why the other choices are wrong", nightmare_prompt)


if __name__ == "__main__":
    unittest.main()
