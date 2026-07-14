import json
import logging
import os
import time
import unicodedata

import streamlit as st

import adaptive
import analytics
from ui import (
    NAVIGATION_OPTIONS,
    apply_official_theme,
    render_dashboard,
    render_navigation,
)
from ui.results import render_review_intro


APP_TITLE = "Universal Learning Engine"
APP_DESCRIPTION = "학습할 주제를 입력하면 동일한 학습 엔진이 해당 주제에 맞게 동작합니다."
DEFAULT_MODEL = "gpt-4.1-mini"
API_TIMEOUT_SECONDS = 60.0
MAX_TOPIC_LENGTH = 80
QUESTION_COUNT_OPTIONS = [5, 10, 15, 20]
DIFFICULTY_OPTIONS = ["Easy", "Normal", "Hard", "Nightmare"]
CONFIDENCE_OPTIONS = {
    "선택 안 함": None,
    "낮음": "low",
    "보통": "medium",
    "높음": "high",
}
NON_RETRYABLE_API_ERROR_KEYWORDS = [
    "authentication",
    "api key",
    "apikey",
    "invalid_api_key",
    "incorrect api key",
    "unauthorized",
    "permission",
    "forbidden",
    "quota",
    "insufficient_quota",
    "billing",
    "payment",
    "rate limit",
    "rate_limit",
]
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404, 429}
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
AI_RESPONSE_FORMAT_ERROR = "AI 응답 형식 오류입니다. 다시 시도해주세요."
AI_RESPONSE_DATA_ERROR = "AI 응답 데이터가 예상과 다릅니다. 다시 시도해주세요."
LOGGER = logging.getLogger("universal_learning_engine")


class ResponseFormatError(ValueError):
    """Model text could not be reduced to one unambiguous JSON object."""


class ResponseValidationError(ValueError):
    """Model JSON violated the preserved lesson contract."""


class ApiRequestError(RuntimeError):
    """The external API request failed after the approved fallback policy."""


class ConfigurationError(RuntimeError):
    """Required local or deployment configuration is unavailable."""


def load_local_env() -> None:
    """Load local environment variables from python-dotenv or a simple .env file."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
        return
    except ImportError:
        pass

    env_path = ".env"
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


def configure_logging() -> None:
    """Configure concise operational logs once without recording learner content."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    LOGGER.setLevel(level)


def get_secret_value(key: str) -> str | None:
    """Read a value from Streamlit Secrets without breaking local execution."""
    try:
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass
    return None


def get_api_key() -> str | None:
    return os.getenv("OPENAI_API_KEY") or get_secret_value("OPENAI_API_KEY")


def get_model() -> str:
    return os.getenv("OPENAI_MODEL") or get_secret_value("OPENAI_MODEL") or DEFAULT_MODEL


def get_quality_difficulty_rules(difficulty: str) -> str:
    """Return stricter v0.3.1 prompt rules for noticeably different difficulty levels."""
    rules = {
        "Easy": """
Easy difficulty:
- Ask definition-style questions.
- Focus on basic terms and beginner concepts.
- The correct answer may be relatively clear.
- Distractors should be simple but not duplicated.
""",
        "Normal": """
Normal difficulty:
- Ask concept-understanding questions.
- Include basic application.
- Include simple comparison between related ideas.
- Avoid making every question pure memorization.
""",
        "Hard": """
Hard difficulty:
- Use application, comparison, and case-based reasoning.
- Do not ask simple definition-only questions.
- Each question must connect at least 2 concepts.
- All 4 choices must be plausible distractors.
- Avoid obvious wrong-answer clues such as excessive "always", "never", "only", or "must".
- The correct answer should not be visually or semantically obvious.
- Prefer exam-style or real-use judgment questions.
""",
        "Nightmare": """
Nightmare difficulty:
- Use complex scenario, multi-step reasoning, trap choices, real-world judgment, and competing trade-offs.
- Every CBT question must include a concrete scenario sentence.
- Do not ask questions solvable by simple memorization.
- Each question must connect at least 3 concepts.
- All wrong choices must sound partially correct or tempting.
- Include traps where the learner must distinguish the best answer from plausible alternatives.
- The explanation must state why the correct answer is best and why the other choices are wrong.
""",
    }
    return rules.get(difficulty, rules["Easy"])


def build_prompt(topic: str, question_count: int, difficulty: str) -> str:
    difficulty_rules = get_quality_difficulty_rules(difficulty)
    return f"""
너는 Universal Learning Engine v0.2이다.

목표:
입력된 학습 주제 하나를 대상으로 MVP 학습 Flow를 생성한다.

학습 주제:
{topic}

CBT 문제 수:
{question_count}

난이도:
{difficulty}

난이도별 출제 기준:
{difficulty_rules}

v0.3.1 CBT 품질 규칙:
- 모든 CBT 문제는 선택지 4개를 가진다.
- choices 배열 안의 선택지 텍스트는 서로 중복되면 안 된다.
- answer_index는 반드시 0, 1, 2, 3 중 하나다.
- 정답이 너무 노골적으로 보이면 안 된다.
- "항상", "무조건", "절대", "오직" 같은 쉬운 오답 단서를 남발하지 않는다.
- Hard와 Nightmare에서는 단순 정의형 문제를 출제하지 않는다.
- Nightmare 문제에는 반드시 구체적인 사례 문장이 포함되어야 한다.
- 해설은 정답 이유와 오답이 틀린 이유를 함께 설명한다.

규칙:
- 주제별 하드코딩 없이 입력 주제에 맞게 일반적으로 설명한다.
- 확장 기능을 만들지 않는다.
- Recovery Engine, Analytics, Dashboard, Decision Engine, Expansion Pack 내용을 넣지 않는다.
- CBT는 반드시 {question_count}문제만 만든다.
- CBT 난이도는 반드시 {difficulty} 수준으로 맞춘다.
- 위 난이도별 출제 기준을 CBT 문제, 선택지, 해설에 강하게 반영한다.
- CBT는 객관식 4지선다로 만든다.
- 완전 초보자도 이해할 수 있게 쓴다.
- 응답은 JSON만 출력한다.

JSON 형식:
{{
  "topic": "학습 주제",
  "tutorial": "가장 기초 개념 설명",
  "example": "쉽게 이해할 수 있는 예제",
  "direct_task": "사용자가 직접 구현하거나 직접 작성할 과제",
  "practice": "간단한 실습 문제",
  "cbt": [
    {{
      "question": "문제",
      "choices": ["선택지1", "선택지2", "선택지3", "선택지4"],
      "answer_index": 0,
      "explanation": "해설"
    }}
  ]
}}
"""


def extract_text(response) -> str:
    if hasattr(response, "output_text"):
        text = response.output_text
    elif hasattr(response, "choices"):
        try:
            text = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise ResponseFormatError(AI_RESPONSE_FORMAT_ERROR) from exc
    else:
        text = str(response)

    if not isinstance(text, str) or not text.strip():
        raise ResponseFormatError(AI_RESPONSE_FORMAT_ERROR)
    return text


def parse_json_response(text: str) -> dict:
    """Parse plain, fenced, or lightly wrapped text as one JSON object."""
    cleaned = str(text).strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ResponseFormatError(AI_RESPONSE_FORMAT_ERROR)
        return parsed
    except json.JSONDecodeError as original_error:
        decoder = json.JSONDecoder()
        objects = []
        search_from = 0
        while True:
            json_start = cleaned.find("{", search_from)
            if json_start == -1:
                break
            try:
                candidate, json_end = decoder.raw_decode(cleaned, json_start)
            except json.JSONDecodeError:
                search_from = json_start + 1
                continue
            if isinstance(candidate, dict):
                objects.append(candidate)
            search_from = max(json_end, json_start + 1)

        if len(objects) == 1:
            return objects[0]
        reason = "multiple_json_objects" if len(objects) > 1 else "json_object_missing"
        LOGGER.warning("json_parse_rejected reason=%s", reason)
        raise ResponseFormatError(AI_RESPONSE_FORMAT_ERROR) from original_error


def build_api_error_message() -> str:
    """Return a stable user message without exposing provider exception text."""
    return (
        "OpenAI API 호출에 실패했습니다. "
        "API 키, 결제 상태, 모델 이름, 네트워크 연결을 확인해주세요."
    )


def should_try_api_fallback(error: Exception) -> bool:
    """Return True only when a second OpenAI API call is likely useful."""
    status_code = getattr(error, "status_code", None)
    if status_code in NON_RETRYABLE_STATUS_CODES:
        return False

    error_text = f"{type(error).__name__} {error}".lower()
    if any(keyword in error_text for keyword in NON_RETRYABLE_API_ERROR_KEYWORDS):
        return False
    if status_code in RETRYABLE_STATUS_CODES:
        return True

    retryable_keywords = ["connection", "timeout", "temporarily", "server", "service unavailable"]
    return any(keyword in error_text for keyword in retryable_keywords)


def build_response_data_error(reason: str) -> str:
    return f"{AI_RESPONSE_DATA_ERROR} 원인: {reason}"


def user_facing_error_message(error: Exception) -> str:
    """Expose only errors intentionally designed for learner display."""
    if isinstance(
        error,
        (ApiRequestError, ConfigurationError, ResponseFormatError, ResponseValidationError),
    ):
        return str(error)
    return "학습 내용을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."


def normalize_choice_text(value: str) -> str:
    """Normalize choice identity without changing the rendered source text."""
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.strip().casefold().split())


def is_correct_answer(selected_index: int, answer_index: int) -> bool:
    """Compare answers by index so duplicate choice text cannot cause misgrading."""
    return (
        type(selected_index) is int
        and type(answer_index) is int
        and selected_index == answer_index
    )


def generate_lesson(topic: str, question_count: int, difficulty: str) -> dict:
    api_key = get_api_key()
    if not api_key:
        raise ConfigurationError("OPENAI_API_KEY가 설정되어 있지 않습니다. 로컬에서는 .env, Streamlit Cloud에서는 Secrets를 설정해주세요.")
    if difficulty not in DIFFICULTY_OPTIONS:
        raise ResponseValidationError(build_response_data_error("지원하지 않는 난이도입니다."))
    if type(question_count) is not int or question_count not in QUESTION_COUNT_OPTIONS:
        raise ResponseValidationError(build_response_data_error("지원하지 않는 CBT 문제 수입니다."))

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ConfigurationError("openai 패키지가 설치되어 있지 않습니다. requirements.txt를 설치해주세요.") from exc

    client = OpenAI(
        api_key=api_key,
        timeout=API_TIMEOUT_SECONDS,
        max_retries=0,
    )
    model = get_model()
    prompt = build_prompt(topic, question_count, difficulty)
    started_at = time.perf_counter()
    LOGGER.info(
        "lesson_generation_started model=%s question_count=%s difficulty=%s",
        model,
        question_count,
        difficulty,
    )

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=0.2,
        )
    except Exception as first_error:
        status_code = getattr(first_error, "status_code", None)
        retryable = should_try_api_fallback(first_error)
        LOGGER.warning(
            "primary_api_failed error_type=%s status_code=%s fallback=%s",
            type(first_error).__name__,
            status_code,
            retryable,
        )
        if not retryable:
            raise ApiRequestError(build_api_error_message()) from first_error
        try:
            LOGGER.info("compatibility_fallback_started model=%s", model)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        except Exception as second_error:
            LOGGER.warning(
                "fallback_api_failed error_type=%s status_code=%s",
                type(second_error).__name__,
                getattr(second_error, "status_code", None),
            )
            raise ApiRequestError(build_api_error_message()) from second_error

    try:
        data = parse_json_response(extract_text(response))
        validate_lesson(data, question_count)
    except (ResponseFormatError, ResponseValidationError) as exc:
        LOGGER.warning("lesson_response_rejected error_type=%s", type(exc).__name__)
        raise
    data["difficulty"] = difficulty
    data["requested_question_count"] = question_count
    LOGGER.info(
        "lesson_generation_completed duration_ms=%s question_count=%s",
        round((time.perf_counter() - started_at) * 1000),
        len(data["cbt"]),
    )
    return data


def validate_lesson(data: dict, question_count: int) -> None:
    """Validate and normalize the lesson JSON returned by the AI model."""
    if type(question_count) is not int or question_count not in QUESTION_COUNT_OPTIONS:
        raise ResponseValidationError(build_response_data_error("지원하지 않는 CBT 문제 수입니다."))
    if not isinstance(data, dict):
        raise ResponseValidationError(build_response_data_error("응답이 객체 형식이 아닙니다."))

    required_keys = ["topic", "tutorial", "example", "direct_task", "practice", "cbt"]
    for key in required_keys:
        if key not in data:
            raise ResponseValidationError(build_response_data_error(f"필요한 값이 없습니다({key})."))

    text_keys = ["topic", "tutorial", "example", "direct_task", "practice"]
    for key in text_keys:
        if not isinstance(data[key], str) or not data[key].strip():
            raise ResponseValidationError(build_response_data_error(f"{key} 값이 비어 있거나 문자 형식이 아닙니다."))

    if not isinstance(data["cbt"], list):
        raise ResponseValidationError(build_response_data_error("CBT 문제가 배열 형식이 아닙니다."))

    actual_question_count = len(data["cbt"])
    if actual_question_count == 0:
        raise ResponseValidationError(build_response_data_error("생성된 CBT 문제가 없습니다. 다시 시도해주세요."))
    if actual_question_count < question_count:
        data["cbt_count_notice"] = (
            f"요청한 문제 수는 {question_count}문제였지만 "
            f"AI가 {actual_question_count}문제만 생성했습니다. "
            "생성된 문제로 학습을 진행합니다."
        )
    elif actual_question_count > question_count:
        data["cbt"] = data["cbt"][:question_count]
        data["cbt_count_notice"] = (
            f"AI가 {actual_question_count}문제를 생성했습니다. "
            f"요청한 {question_count}문제만 사용합니다."
        )

    for index, question in enumerate(data["cbt"], start=1):
        if not isinstance(question, dict):
            raise ResponseValidationError(build_response_data_error(f"CBT {index}번 문제가 객체 형식이 아닙니다."))
        for key in ["question", "choices", "answer_index", "explanation"]:
            if key not in question:
                raise ResponseValidationError(build_response_data_error(f"CBT {index}번 문제에 {key} 값이 없습니다."))
        if not isinstance(question["question"], str) or not question["question"].strip():
            raise ResponseValidationError(build_response_data_error(f"CBT {index}번 문제 내용이 비어 있습니다."))
        if not isinstance(question["choices"], list) or len(question["choices"]) != 4:
            raise ResponseValidationError(build_response_data_error(f"CBT {index}번 문제는 선택지 4개가 필요합니다."))
        if not all(isinstance(choice, str) and choice.strip() for choice in question["choices"]):
            raise ResponseValidationError(build_response_data_error(f"CBT {index}번 선택지가 비어 있거나 문자 형식이 아닙니다."))
        normalized_choices = [normalize_choice_text(choice) for choice in question["choices"]]
        if len(set(normalized_choices)) != len(normalized_choices):
            raise ResponseValidationError(build_response_data_error(f"CBT {index}번 문제에 중복 선택지가 있습니다."))
        answer_index = question.get("answer_index")
        if type(answer_index) is not int or answer_index not in [0, 1, 2, 3]:
            raise ResponseValidationError(build_response_data_error(f"CBT {index}번 문제의 정답 번호가 올바르지 않습니다."))
        if not isinstance(question["explanation"], str) or not question["explanation"].strip():
            raise ResponseValidationError(build_response_data_error(f"CBT {index}번 해설이 비어 있습니다."))


def validate_topic_input(topic: str) -> tuple[bool, str, str]:
    cleaned_topic = topic.strip()
    if not cleaned_topic:
        return False, "", "학습할 주제를 입력해주세요."
    if len(cleaned_topic) > MAX_TOPIC_LENGTH:
        return False, "", f"학습 주제는 {MAX_TOPIC_LENGTH}자 이하로 입력해주세요."
    return True, cleaned_topic, ""


def reset_round_state() -> None:
    st.session_state.answers = {}
    st.session_state.answer_confidence = {}
    st.session_state.current_question_index = 0
    st.session_state.current_feedback = None
    st.session_state.round_finished = False
    current_round_id = st.session_state.get("cbt_round_id", 0)
    st.session_state.cbt_round_id = current_round_id + 1
    for key in list(st.session_state.keys()):
        is_cbt_widget = key.startswith("cbt_") and key != "cbt_round_id"
        if is_cbt_widget or key.startswith("confidence_"):
            del st.session_state[key]


def reset_learning_state(clear_adaptation: bool = True) -> None:
    st.session_state.lesson = None
    reset_round_state()
    st.session_state.pending_view = "Dashboard"
    st.session_state.navigation_explicit = False
    if clear_adaptation:
        st.session_state.adaptation_records = {}
        st.session_state.latest_adaptive_summary = None
        st.session_state.adaptation_error = None
        st.session_state.pending_recommended_difficulty = None
        st.session_state.analytics_cache = None
        st.session_state.analytics_revision = 0


def mark_navigation_explicit() -> None:
    """Remember that Dashboard navigation was chosen by the learner."""
    st.session_state.navigation_explicit = True


def apply_pending_view() -> None:
    """Apply queued navigation before the keyed navigation widget is created."""
    pending = st.session_state.pending_view
    if pending in NAVIGATION_OPTIONS:
        st.session_state.active_view = pending
    st.session_state.pending_view = None


def init_state() -> None:
    """Initialize and repair Streamlit session state used by the learning flow."""
    defaults = {
        "lesson": None,
        "answers": {},
        "answer_confidence": {},
        "current_question_index": 0,
        "current_feedback": None,
        "round_finished": False,
        "cbt_round_id": 0,
        "is_generating": False,
        "adaptation_records": {},
        "latest_adaptive_summary": None,
        "adaptation_error": None,
        "pending_recommended_difficulty": None,
        "analytics_cache": None,
        "analytics_revision": 0,
        "active_view": "Dashboard",
        "pending_view": None,
        "navigation_explicit": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, dict) else value

    if st.session_state.lesson is not None and not isinstance(st.session_state.lesson, dict):
        st.session_state.lesson = None
    if not isinstance(st.session_state.answers, dict):
        st.session_state.answers = {}
    if not isinstance(st.session_state.answer_confidence, dict):
        st.session_state.answer_confidence = {}
    if type(st.session_state.current_question_index) is not int:
        st.session_state.current_question_index = 0
    if st.session_state.current_feedback is not None and not isinstance(
        st.session_state.current_feedback, dict
    ):
        st.session_state.current_feedback = None
    if not isinstance(st.session_state.round_finished, bool):
        st.session_state.round_finished = False
    if type(st.session_state.cbt_round_id) is not int or st.session_state.cbt_round_id < 0:
        st.session_state.cbt_round_id = 0
    if not isinstance(st.session_state.is_generating, bool):
        st.session_state.is_generating = False
    if not isinstance(st.session_state.adaptation_records, dict):
        st.session_state.adaptation_records = {}
    if st.session_state.latest_adaptive_summary is not None and not isinstance(
        st.session_state.latest_adaptive_summary, dict
    ):
        st.session_state.latest_adaptive_summary = None
    if st.session_state.adaptation_error not in (None, "adaptive_summary_failed"):
        st.session_state.adaptation_error = None
    if st.session_state.pending_recommended_difficulty not in (
        None,
        *DIFFICULTY_OPTIONS,
    ):
        st.session_state.pending_recommended_difficulty = None
    if st.session_state.analytics_cache is not None and not isinstance(
        st.session_state.analytics_cache, dict
    ):
        st.session_state.analytics_cache = None
    if type(st.session_state.analytics_revision) is not int or st.session_state.analytics_revision < 0:
        st.session_state.analytics_revision = 0
    if st.session_state.active_view not in NAVIGATION_OPTIONS:
        st.session_state.active_view = "Dashboard"
    if st.session_state.pending_view not in (None, *NAVIGATION_OPTIONS):
        st.session_state.pending_view = None
    if not isinstance(st.session_state.navigation_explicit, bool):
        st.session_state.navigation_explicit = False

def apply_pending_difficulty_recommendation() -> None:
    """Apply a queued recommendation before Streamlit creates the selector widget."""
    pending = st.session_state.pending_recommended_difficulty
    if pending in DIFFICULTY_OPTIONS:
        st.session_state.difficulty_selector = pending
    st.session_state.pending_recommended_difficulty = None


def normalize_round_state(lesson: dict) -> None:
    questions = lesson.get("cbt", [])
    total_questions = len(questions)
    if total_questions == 0:
        reset_round_state()
        return

    if not isinstance(st.session_state.answers, dict):
        st.session_state.answers = {}

    safe_answers = {}
    for key, value in st.session_state.answers.items():
        if (
            type(key) is int
            and 0 <= key < total_questions
            and type(value) is int
            and value in [0, 1, 2, 3]
        ):
            safe_answers[key] = value
    st.session_state.answers = safe_answers

    if not isinstance(st.session_state.answer_confidence, dict):
        st.session_state.answer_confidence = {}
    st.session_state.answer_confidence = {
        key: adaptive.normalize_confidence(value)
        for key, value in st.session_state.answer_confidence.items()
        if type(key) is int and 0 <= key < total_questions
    }

    if type(st.session_state.current_question_index) is not int:
        st.session_state.current_question_index = 0
    st.session_state.current_question_index = max(
        0,
        min(st.session_state.current_question_index, total_questions - 1),
    )

    if not isinstance(st.session_state.round_finished, bool):
        st.session_state.round_finished = False

    feedback = st.session_state.current_feedback
    if not isinstance(feedback, dict):
        st.session_state.current_feedback = None
        return

    feedback_index = feedback.get("index")
    selected_index = feedback.get("selected_index")
    if (
        type(feedback_index) is not int
        or feedback_index < 0
        or feedback_index >= total_questions
        or type(selected_index) is not int
        or selected_index not in [0, 1, 2, 3]
        or not isinstance(feedback.get("is_correct"), bool)
    ):
        st.session_state.current_feedback = None


def normalize_topic_key(topic: str) -> str:
    """Normalize a topic only for session-local record grouping."""
    return " ".join(str(topic).strip().casefold().split())


def confidence_input_to_value(label: str) -> str | None:
    """Translate the optional Korean UI label to the adaptive data contract."""
    return CONFIDENCE_OPTIONS.get(label)


def calculate_learning_progress(records: list[dict]) -> dict:
    """Compare completed rounds without claiming long-term retention."""
    if not records:
        return {
            "completed_rounds": 0,
            "latest_accuracy": None,
            "previous_accuracy": None,
            "accuracy_change": None,
            "trend": "not_available",
        }
    latest = records[-1]["round_status"]["accuracy"]
    previous = records[-2]["round_status"]["accuracy"] if len(records) > 1 else None
    change = latest - previous if previous is not None else None
    if change is None:
        trend = "not_available"
    elif change > 0:
        trend = "improved"
    elif change < 0:
        trend = "declined"
    else:
        trend = "steady"
    return {
        "completed_rounds": len(records),
        "latest_accuracy": latest,
        "previous_accuracy": previous,
        "accuracy_change": change,
        "trend": trend,
    }


def record_completed_round(lesson: dict) -> dict:
    """Atomically record one completed round and invalidate derived analytics."""
    topic_key = normalize_topic_key(lesson["topic"])
    round_id = st.session_state.cbt_round_id
    source_records = st.session_state.adaptation_records.get(topic_key, [])
    records = source_records if isinstance(source_records, list) else []
    existing = next(
        (
            item
            for item in records
            if isinstance(item, dict)
            and isinstance(item.get("round_status"), dict)
            and item["round_status"].get("round_id") == round_id
        ),
        None,
    )
    if existing is not None:
        return existing

    answer_evidence = []
    for index, question in enumerate(lesson["cbt"]):
        selected_index = st.session_state.answers.get(index)
        answer_evidence.append(
            {
                "question_index": index,
                "selected_index": selected_index,
                "answer_index": question["answer_index"],
                "is_correct": is_correct_answer(selected_index, question["answer_index"]),
                "confidence": st.session_state.answer_confidence.get(index),
            }
        )
    status = adaptive.build_round_status(
        answer_evidence,
        lesson.get("difficulty", "Easy"),
        round_id,
        topic_key,
    )
    summary = adaptive.build_adaptive_summary(status)
    next_records = [*records, summary]
    summary["learning_progress"] = calculate_learning_progress(next_records)
    next_adaptation_records = dict(st.session_state.adaptation_records)
    next_adaptation_records[topic_key] = next_records
    next_revision = st.session_state.analytics_revision + 1

    st.session_state.adaptation_records = next_adaptation_records
    st.session_state.analytics_revision = next_revision
    st.session_state.analytics_cache = None
    return summary

def get_cached_learning_analytics(topic_key: str) -> dict:
    """Reuse analytics until completed-round evidence changes."""
    cache = st.session_state.analytics_cache
    revision = st.session_state.analytics_revision
    if (
        isinstance(cache, dict)
        and cache.get("topic_key") == topic_key
        and cache.get("revision") == revision
        and isinstance(cache.get("result"), dict)
    ):
        return cache["result"]

    result = analytics.build_learning_analytics(
        st.session_state.adaptation_records,
        topic_key,
    )
    st.session_state.analytics_cache = {
        "topic_key": topic_key,
        "revision": revision,
        "result": result,
    }
    return result


def render_learning_status(lesson: dict) -> None:
    topic = lesson.get("topic", "학습 주제")
    difficulty = lesson.get("difficulty", "Easy")
    requested_count = lesson.get("requested_question_count", len(lesson.get("cbt", [])))

    st.info(
        f"학습 주제: {topic} | "
        f"난이도: {difficulty} | "
        f"문제 수: {requested_count}"
    )


def render_lesson(lesson: dict) -> None:
    st.header(f"학습 주제: {lesson['topic']}")
    render_learning_status(lesson)

    if lesson.get("cbt_count_notice"):
        st.warning(lesson["cbt_count_notice"])

    st.subheader("튜토리얼")
    st.write(lesson["tutorial"])

    st.subheader("예제")
    st.write(lesson["example"])

    st.subheader("직접 구현 / 직접 작성")
    st.write(lesson["direct_task"])
    st.text_area("직접 작성해보세요.", key="direct_input")

    st.subheader("실습")
    st.write(lesson["practice"])
    st.text_area("실습 답안을 작성해보세요.", key="practice_input")

    render_cbt(lesson)


def render_cbt(lesson: dict) -> None:
    normalize_round_state(lesson)
    questions = lesson["cbt"]
    total_questions = len(questions)
    if total_questions == 0:
        st.error("CBT 문제가 없습니다. 학습을 다시 시작해주세요.")
        return

    current_index = min(st.session_state.current_question_index, total_questions - 1)
    question = questions[current_index]

    st.subheader("CBT")
    st.write(f"난이도: {lesson.get('difficulty', 'Easy')}")
    progress_current = total_questions if st.session_state.round_finished else current_index + 1
    st.write(f"진행률: {progress_current} / {total_questions}")
    st.progress(progress_current / total_questions)

    if st.session_state.round_finished:
        try:
            st.session_state.latest_adaptive_summary = record_completed_round(lesson)
            st.session_state.adaptation_error = None
        except Exception as exc:
            st.session_state.latest_adaptive_summary = None
            st.session_state.adaptation_error = "adaptive_summary_failed"
            LOGGER.warning(
                "adaptive_summary_failed error_type=%s",
                type(exc).__name__,
            )
        render_round_summary(lesson)
        if st.button("다시 학습"):
            reset_round_state()
            st.rerun()
        if st.button("처음으로"):
            reset_learning_state()
            st.rerun()
        return

    st.markdown(f"**문제 {current_index + 1} / {total_questions}. {question['question']}**")
    feedback = st.session_state.current_feedback
    answer_locked = (
        isinstance(feedback, dict)
        and feedback.get("index") == current_index
        and current_index in st.session_state.answers
    )
    selected_index = st.radio(
        "답을 선택하세요.",
        range(len(question["choices"])),
        format_func=lambda index: question["choices"][index],
        key=f"cbt_{st.session_state.cbt_round_id}_{current_index}",
        index=None,
        disabled=answer_locked,
    )
    confidence_label = st.selectbox(
        "답변 확신도 (선택)",
        list(CONFIDENCE_OPTIONS),
        key=f"confidence_{st.session_state.cbt_round_id}_{current_index}",
        help="현재 답변에 대해 스스로 느끼는 확신도입니다. 선택하지 않아도 됩니다.",
        disabled=answer_locked,
    )

    if st.button("정답 확인", disabled=answer_locked):
        if selected_index is None:
            st.warning("답을 선택해주세요.")
        else:
            is_correct = is_correct_answer(selected_index, question["answer_index"])
            st.session_state.answers[current_index] = selected_index
            st.session_state.answer_confidence[current_index] = confidence_input_to_value(
                confidence_label
            )
            st.session_state.current_feedback = {
                "index": current_index,
                "is_correct": is_correct,
                "selected_index": selected_index,
            }
            st.rerun()

    render_current_feedback(question, current_index, total_questions)


def render_current_feedback(question: dict, current_index: int, total_questions: int) -> None:
    feedback = st.session_state.current_feedback
    if not feedback or feedback["index"] != current_index:
        return

    if feedback["is_correct"]:
        st.success("정답입니다.")
    else:
        st.error("오답입니다.")

    st.write(f"정답: {question['choices'][question['answer_index']]}")
    st.write(f"해설: {question['explanation']}")

    if current_index < total_questions - 1:
        if st.button("다음 문제"):
            st.session_state.current_question_index += 1
            st.session_state.current_feedback = None
            st.rerun()
    else:
        if st.button("결과 보기"):
            st.session_state.round_finished = True
            st.session_state.current_feedback = None
            st.rerun()


def render_round_summary(lesson: dict) -> None:
    questions = lesson["cbt"]
    total_questions = len(questions)
    correct_count = 0
    wrong_answers = []

    for index, question in enumerate(questions):
        user_answer = st.session_state.answers.get(index)
        if user_answer == question["answer_index"]:
            correct_count += 1
        else:
            wrong_answers.append((index, question, user_answer))

    wrong_count = total_questions - correct_count
    accuracy = round((correct_count / total_questions) * 100) if total_questions else 0

    st.subheader("라운드 결과 요약")
    result_columns = st.columns(4)
    result_columns[0].metric("정답률", f"{accuracy}%")
    result_columns[1].metric("정답", correct_count)
    result_columns[2].metric("오답", wrong_count)
    result_columns[3].metric("난이도", lesson.get("difficulty", "Easy"))

    st.subheader("오답노트")
    if not wrong_answers:
        st.success("틀린 문제가 없습니다.")
    else:
        with st.expander(f"오답 {wrong_count}개 자세히 보기"):
            for index, question, user_answer in wrong_answers:
                st.markdown(f"**문제 {index + 1}. {question['question']}**")
                if user_answer is None:
                    st.write("사용자 답: 미응답")
                else:
                    st.write(f"사용자 답: {question['choices'][user_answer]}")
                st.write(f"정답: {question['choices'][question['answer_index']]}")

    st.subheader("해설")
    with st.expander(f"전체 {total_questions}개 해설 보기"):
        for index, question in enumerate(questions):
            st.markdown(f"**문제 {index + 1}. {question['question']}**")
            st.write(f"정답: {question['choices'][question['answer_index']]}")
            st.write(question["explanation"])

    st.subheader("학습 종료")
    st.success("학습이 완료되었습니다.")

    render_adaptive_summary()
    render_learning_analytics(lesson)


def render_adaptive_summary() -> None:
    """Render additive v0.4 advice without replacing the v0.3.1 result."""
    if st.session_state.adaptation_error:
        st.warning(
            "기존 학습 결과는 정상적으로 완료되었지만 적응형 분석을 표시할 수 없습니다."
        )
        return
    summary = st.session_state.latest_adaptive_summary
    if not summary:
        return

    status = summary["round_status"]
    confidence = status["confidence_counts"]
    progress = summary["learning_progress"]
    difficulty = summary["difficulty_recommendation"]
    recovery = summary["recovery_recommendation"]

    st.divider()
    st.header("v0.4 적응형 학습 안내")
    st.caption("현재 세션과 현재 주제의 결과만 사용한 참고용 추천입니다.")

    st.subheader("라운드 상태")
    st.write(
        f"난이도 {status['difficulty']} | 정답 {status['correct_count']} / "
        f"{status['question_count']} | 정확도 {status['accuracy']:.0f}%"
    )
    st.write(
        "보고된 확신도 — "
        f"높음 {confidence.get('high', 0)}, 보통 {confidence.get('medium', 0)}, "
        f"낮음 {confidence.get('low', 0)}, 미선택 {confidence.get('unset', 0)}"
    )

    st.subheader("학습 패턴")
    pattern_labels = {
        "strong_mastery_signal": "강한 숙달 신호",
        "fragile_success_signal": "불안정한 성공 신호",
        "overconfidence_risk": "과신 위험 신호",
        "developing_understanding": "발전 중인 이해",
        "foundational_gap_signal": "기초 보완 신호",
    }
    for signal in summary["learning_patterns"]:
        st.write(f"- {pattern_labels.get(signal['name'], signal['name'])}: {signal['reason']}")

    st.subheader("학습 진행")
    st.write(f"이 세션에서 같은 주제로 완료한 라운드: {progress['completed_rounds']}")
    if progress["accuracy_change"] is None:
        st.write("이전 라운드가 없어 정확도 변화는 아직 계산하지 않습니다.")
    else:
        st.write(
            f"이전 라운드 대비 정확도 변화: {progress['accuracy_change']:+.0f}%p "
            f"({progress['trend']})"
        )

    st.subheader("다음 난이도 추천")
    st.write(
        f"현재 {difficulty['current_difficulty']} → 추천 "
        f"{difficulty['recommended_difficulty']}"
    )
    st.write(difficulty["reason"])
    st.caption(difficulty["advisory"])
    if difficulty["recommended_difficulty"] != difficulty["current_difficulty"]:
        if st.button("추천 난이도 사용", key="apply_recommended_difficulty"):
            st.session_state.pending_recommended_difficulty = difficulty[
                "recommended_difficulty"
            ]
            st.rerun()
    else:
        st.info("현재 난이도를 유지하는 것을 추천합니다.")

    st.subheader("회복 학습 추천")
    st.write(f"우선순위: {recovery['priority']} | {recovery['interval']}")
    st.write(recovery["reason"])
    st.caption(recovery["advisory"])


def _format_analytics_percentage(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}%"


def _analytics_round_rows(rounds: list[dict]) -> list[dict]:
    return [
        {
            "주제": item["topic_key"],
            "라운드": item["round_id"],
            "난이도": item["difficulty"],
            "문항": item["question_count"],
            "정답": item["correct_count"],
            "정확도": _format_analytics_percentage(item["accuracy"]),
            "확신도 보고율": _format_analytics_percentage(
                item["confidence"]["reporting_rate"]
            ),
        }
        for item in rounds
    ]


def _analytics_aggregate_rows(items: list[dict], key_label: str) -> list[dict]:
    return [
        {
            key_label: item["scope_key"],
            "라운드": item["round_count"],
            "문항": item["question_count"],
            "가중 정확도": _format_analytics_percentage(item["weighted_accuracy"]),
            "평균 라운드 정확도": _format_analytics_percentage(
                item["mean_round_accuracy"]
            ),
            "확신도 보고율": _format_analytics_percentage(
                item["confidence"]["reporting_rate"]
            ),
        }
        for item in items
    ]


def render_learning_analytics(lesson: dict) -> None:
    """Render additive v0.5 analytics without affecting the v0.4 result path."""
    try:
        topic_key = normalize_topic_key(lesson["topic"])
        result = get_cached_learning_analytics(topic_key)
    except Exception as exc:
        LOGGER.warning(
            "learning_analytics_failed error_type=%s",
            type(exc).__name__,
        )
        st.warning(
            "기존 v0.4 학습 결과는 정상적으로 완료되었지만 "
            "v0.5 학습 분석을 표시할 수 없습니다."
        )
        return

    latest = result["latest_round"]
    current = result["current_topic"]
    overall = result["overall"]

    st.divider()
    st.header("v0.5 학습 분석")
    st.caption(
        "현재 Streamlit 세션에 남아 있는 완료 라운드만 사용한 설명형 분석입니다. "
        "결정, 자동 실행, 저장 또는 일정 생성을 수행하지 않습니다."
    )

    if latest is None:
        st.info("현재 주제에서 분석할 완료 라운드가 없습니다.")
        return

    st.subheader("최신 라운드 분석")
    latest_columns = st.columns(4)
    latest_columns[0].metric("정확도", _format_analytics_percentage(latest["accuracy"]))
    latest_columns[1].metric(
        "확신도 보고율",
        _format_analytics_percentage(latest["confidence"]["reporting_rate"]),
    )
    latest_columns[2].metric(
        "근거 있는 성공",
        _format_analytics_percentage(
            latest["answer_patterns"]["supported_success_rate"]
        ),
    )
    latest_columns[3].metric(
        "확신한 오답",
        _format_analytics_percentage(
            latest["answer_patterns"]["confident_error_rate"]
        ),
    )

    st.subheader("세션 분석 — 현재 주제")
    current_columns = st.columns(4)
    current_columns[0].metric("완료 라운드", current["round_count"])
    current_columns[1].metric("분석 문항", current["question_count"])
    current_columns[2].metric(
        "가중 정확도", _format_analytics_percentage(current["weighted_accuracy"])
    )
    current_columns[3].metric(
        "최근 변화",
        "—"
        if current["latest_change"] is None
        else f"{current['latest_change']:+.1f}%p",
    )
    st.write(current["learning_summary"]["headline"])
    st.caption(
        "가중 정확도는 모든 정답 수를 모든 문항 수로 나눈 값입니다. "
        f"평균 라운드 정확도: {_format_analytics_percentage(current['mean_round_accuracy'])}"
    )

    st.subheader("전체 학습 분석 — 현재 세션")
    overall_columns = st.columns(4)
    overall_columns[0].metric("보존된 주제", overall["topic_count"])
    overall_columns[1].metric("완료 라운드", overall["round_count"])
    overall_columns[2].metric("분석 문항", overall["question_count"])
    overall_columns[3].metric(
        "가중 정확도", _format_analytics_percentage(overall["weighted_accuracy"])
    )
    st.write(overall["learning_summary"]["headline"])
    st.caption(
        f"전체 확신도 보고율: {_format_analytics_percentage(overall['confidence']['reporting_rate'])} | "
        f"평균 라운드 정확도: {_format_analytics_percentage(overall['mean_round_accuracy'])}"
    )

    st.subheader("강점 / 약점 요약")
    strengths = overall["concise_strengths"]
    weaknesses = overall["concise_weaknesses"]
    mixed = overall["mixed_evidence"]
    if strengths:
        st.markdown("**현재 증거에서 확인된 강점**")
        for item in strengths:
            st.write(f"- {item['evidence_text']}")
    else:
        st.info("현재 보존된 증거만으로 명확한 강점이 확립되지 않았습니다.")
    if weaknesses:
        st.markdown("**현재 증거에서 확인된 약점**")
        for item in weaknesses:
            reasons = ", ".join(item["matched_rules"])
            st.write(f"- {item['evidence_text']} 근거 규칙: {reasons}")
    else:
        st.info("현재 보존된 증거만으로 명확한 약점이 확립되지 않았습니다.")
    for item in mixed:
        st.warning(f"혼합 증거: {item['evidence_text']}")
    st.caption(
        "강점/약점 표시는 같은 주제·난이도에서 최소 2라운드와 10문항의 "
        "증거가 있을 때만 적용됩니다. 개념별 숙달을 의미하지 않습니다."
    )

    with st.expander("라운드별 분석"):
        st.dataframe(_analytics_round_rows(current["rounds"]), hide_index=True)
    with st.expander("주제별 분석"):
        st.dataframe(
            _analytics_aggregate_rows(overall["topic_summaries"], "주제"),
            hide_index=True,
        )
    with st.expander("난이도별 분석"):
        st.dataframe(
            _analytics_aggregate_rows(overall["difficulty_summaries"], "난이도"),
            hide_index=True,
        )
    with st.expander("확신도 및 학습 패턴 상세"):
        confidence = overall["confidence"]["counts"]
        st.write(
            "보고된 확신도 — "
            f"높음 {confidence['high']}, 보통 {confidence['medium']}, "
            f"낮음 {confidence['low']}, 미선택 {confidence['unset']}"
        )
        if overall["learning_pattern_frequencies"]:
            for name, count in overall["learning_pattern_frequencies"].items():
                st.write(f"- {name}: {count}개 라운드")
        else:
            st.write("표시할 학습 패턴 신호가 없습니다.")
        if overall["skipped_record_count"]:
            st.warning(
                f"유효하지 않은 분석 레코드 {overall['skipped_record_count']}개를 제외했습니다."
            )


def render_learning_setup() -> None:
    """Render the preserved universal-topic lesson controls."""
    st.caption("NEW LEARNING SESSION")
    st.subheader("학습 설정")
    topic = st.text_input(
        "학습할 주제를 입력하세요.",
        placeholder="예: 제과제빵, Python, 영어, 투자, 역사",
    )
    setup_columns = st.columns(2)
    question_count = setup_columns[0].selectbox(
        "CBT 문제 수를 선택하세요.", QUESTION_COUNT_OPTIONS, index=0
    )
    difficulty = setup_columns[1].selectbox(
        "난이도를 선택하세요.",
        DIFFICULTY_OPTIONS,
        index=0,
        key="difficulty_selector",
    )

    if st.button(
        "학습 시작",
        disabled=st.session_state.is_generating,
        type="primary",
        use_container_width=True,
    ):
        is_valid, cleaned_topic, message = validate_topic_input(topic)
        if not is_valid:
            st.warning(message)
            return

        reset_learning_state(clear_adaptation=False)
        st.session_state.is_generating = True
        with st.spinner("학습 내용을 생성하는 중입니다."):
            try:
                st.session_state.lesson = generate_lesson(
                    cleaned_topic, question_count, difficulty
                )
                st.session_state.pending_view = "Learning"
                st.session_state.navigation_explicit = True
            except Exception as exc:
                LOGGER.warning(
                    "lesson_generation_failed error_type=%s",
                    type(exc).__name__,
                )
                st.error(user_facing_error_message(exc))
            finally:
                st.session_state.is_generating = False
        if st.session_state.lesson:
            st.rerun()


def dashboard_analytics() -> dict | None:
    """Return cached session analytics for Dashboard rendering when available."""
    records = st.session_state.adaptation_records
    if not isinstance(records, dict) or not records:
        return None
    lesson = st.session_state.lesson
    if isinstance(lesson, dict):
        topic_key = normalize_topic_key(lesson.get("topic", ""))
    else:
        topic_key = next(reversed(records), "")
    if not topic_key:
        return None
    try:
        return get_cached_learning_analytics(topic_key)
    except Exception as exc:
        LOGGER.warning("dashboard_analytics_failed error_type=%s", type(exc).__name__)
        return None


def render_review() -> None:
    lesson = st.session_state.lesson
    has_result = isinstance(lesson, dict) and st.session_state.round_finished
    if not render_review_intro(st, has_result):
        return
    try:
        st.session_state.latest_adaptive_summary = record_completed_round(lesson)
        st.session_state.adaptation_error = None
    except Exception as exc:
        st.session_state.latest_adaptive_summary = None
        st.session_state.adaptation_error = "adaptive_summary_failed"
        LOGGER.warning("adaptive_summary_failed error_type=%s", type(exc).__name__)
    render_round_summary(lesson)


def main() -> None:
    configure_logging()
    st.set_page_config(
        page_title=f"{APP_TITLE} v1.0",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_state()
    apply_pending_difficulty_recommendation()
    apply_pending_view()

    if (
        st.session_state.lesson
        and st.session_state.active_view == "Dashboard"
        and not st.session_state.navigation_explicit
    ):
        st.session_state.active_view = "Learning"

    apply_official_theme(st)
    st.title(APP_TITLE)
    st.write(APP_DESCRIPTION)
    selected_view = render_navigation(st, on_change=mark_navigation_explicit)
    st.divider()

    if selected_view == "Dashboard":
        render_dashboard(
            st,
            lesson=st.session_state.lesson,
            adaptation_records=st.session_state.adaptation_records,
            latest_summary=st.session_state.latest_adaptive_summary,
            analytics_result=dashboard_analytics(),
        )
        if not st.session_state.lesson:
            st.divider()
            render_learning_setup()
    elif selected_view == "Review":
        render_review()
    else:
        render_learning_setup()
        if st.session_state.lesson:
            st.divider()
            render_lesson(st.session_state.lesson)


if __name__ == "__main__":
    main()
