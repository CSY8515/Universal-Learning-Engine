import json
import logging
import os
import time
import unicodedata
from datetime import date

import streamlit as st

import adaptive
import analytics
import world_state
from expansion import ExpansionAPI
from ui import (
    NAVIGATION_OPTIONS,
    apply_official_theme,
    render_navigation,
)


APP_TITLE = "통합 학습 엔진"
APP_DESCRIPTION = "학습할 주제를 입력하면 동일한 학습 엔진이 해당 주제에 맞게 동작합니다."
DEFAULT_MODEL = "gpt-4.1-mini"
API_TIMEOUT_SECONDS = 60.0
BYOK_API_KEY_STATE = "user_openai_api_key"
BYOK_CONNECTION_STATE = "openai_connection_status"
BYOK_NOTICE_STATE = "openai_api_notice"
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
AI_RESPONSE_FORMAT_ERROR = "인공지능 응답 형식을 확인할 수 없습니다. 다시 시도해주세요."
AI_RESPONSE_DATA_ERROR = "인공지능 응답 내용이 예상과 다릅니다. 다시 시도해주세요."
LOGGER = logging.getLogger("universal_learning_engine")

PRIORITY_LABELS = {"high": "높음", "medium": "보통", "low": "낮음"}
TREND_LABELS = {
    "improving": "향상",
    "declining": "하락",
    "stable": "유지",
    "not_available": "비교 자료 없음",
}
ANALYTICS_RULE_LABELS = {
    "minimum_evidence_not_met": "최소 분석 근거 부족",
    "strength_thresholds_met": "강점 기준 충족",
    "low_weighted_accuracy": "낮은 가중 정확도",
    "confident_error_evidence": "확신한 오답 근거",
    "no_clear_strength_or_weakness": "뚜렷한 강점·약점 없음",
}
PATTERN_LABELS = {
    "strong_mastery_signal": "강한 숙달 신호",
    "fragile_success_signal": "불안정한 성공 신호",
    "overconfidence_risk": "과신 위험 신호",
    "developing_understanding": "발전 중인 이해",
    "foundational_gap_signal": "기초 보완 신호",
}


def localize_system_text(value: object) -> str:
    text = str(value)
    replacements = (
        ("Universal Learning Engine", "통합 학습 엔진"),
        ("Recovery Recommendation", "회복 학습 추천"),
        ("Recovery Session", "회복 학습"),
        ("Challenge Session", "도전 학습"),
        ("Challenge Result", "도전 학습 결과"),
        ("Learning Resource", "학습 자료"),
        ("Planner Schedule", "학습 일정"),
        ("Planner Goal", "학습 목표"),
        ("My Learning", "나의 학습"),
        ("Management", "관리"),
        ("Analytics", "학습 분석"),
        ("Challenge", "도전 학습"),
        ("Recovery", "회복 학습"),
        ("Planner", "학습 계획"),
        ("Library", "학습 자료실"),
        ("Learning", "학습"),
        ("AI", "인공지능"),
        ("Nightmare", "최고 난도"),
        ("Normal", "보통"),
        ("Hard", "심화"),
        ("Easy", "기초"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    return text


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
    try:
        value = st.session_state.get(BYOK_API_KEY_STATE, "")
    except Exception:
        return None
    return normalize_api_key_input(value) or None


def normalize_api_key_input(value: object) -> str:
    """Normalize a session-only BYOK value without exposing or persisting it."""
    if not isinstance(value, str):
        return ""
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 512 or any(char.isspace() for char in cleaned):
        return ""
    return cleaned


def register_api_key(value: object) -> None:
    cleaned = normalize_api_key_input(value)
    if not cleaned:
        raise ConfigurationError("인공지능 연결 키를 확인해주세요.")
    st.session_state[BYOK_API_KEY_STATE] = cleaned
    st.session_state[BYOK_CONNECTION_STATE] = "registered"


def delete_api_key() -> None:
    st.session_state[BYOK_API_KEY_STATE] = ""
    st.session_state[BYOK_CONNECTION_STATE] = "missing"


def get_model() -> str:
    return os.getenv("OPENAI_MODEL") or get_secret_value("OPENAI_MODEL") or DEFAULT_MODEL


def create_openai_client(api_key: str):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ConfigurationError(
            "인공지능 기능을 사용할 수 없습니다. 관리자에게 문의해주세요."
        ) from exc
    return OpenAI(
        api_key=api_key,
        timeout=API_TIMEOUT_SECONDS,
        max_retries=0,
    )


def test_openai_connection(api_key: str) -> bool:
    cleaned = normalize_api_key_input(api_key)
    if not cleaned:
        raise ConfigurationError("먼저 본인의 인공지능 연결 키를 등록해주세요.")
    client = create_openai_client(cleaned)
    try:
        response = client.responses.create(
            model=get_model(),
            input="Reply with OK.",
            max_output_tokens=8,
        )
        extract_text(response)
    except Exception as error:
        LOGGER.warning(
            "byok_connection_test_failed error_type=%s status_code=%s",
            type(error).__name__,
            getattr(error, "status_code", None),
        )
        raise ApiRequestError(build_api_error_message()) from error
    return True


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
- 시스템 내부 기능이나 관리 구조를 학습 내용에 넣지 않는다.
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
        "인공지능 서비스 연결에 실패했습니다. "
        "연결 키, 이용 가능 상태, 네트워크 연결을 확인해주세요."
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
        raise ConfigurationError(
            "본인의 인공지능 연결 키를 관리 화면에서 먼저 등록해주세요."
        )
    if difficulty not in DIFFICULTY_OPTIONS:
        raise ResponseValidationError(build_response_data_error("지원하지 않는 난이도입니다."))
    if type(question_count) is not int or question_count not in QUESTION_COUNT_OPTIONS:
        raise ResponseValidationError(build_response_data_error("지원하지 않는 문제 수입니다."))

    client = create_openai_client(api_key)
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
        raise ResponseValidationError(build_response_data_error("지원하지 않는 문제 수입니다."))
    if not isinstance(data, dict):
        raise ResponseValidationError(build_response_data_error("응답이 객체 형식이 아닙니다."))

    required_keys = ["topic", "tutorial", "example", "direct_task", "practice", "cbt"]
    for key in required_keys:
        if key not in data:
            raise ResponseValidationError(
                build_response_data_error("학습 내용에 필요한 항목이 없습니다.")
            )

    text_keys = ["topic", "tutorial", "example", "direct_task", "practice"]
    for key in text_keys:
        if not isinstance(data[key], str) or not data[key].strip():
            raise ResponseValidationError(
                build_response_data_error(
                    "학습 내용의 문자 항목이 비어 있거나 올바르지 않습니다."
                )
            )

    if not isinstance(data["cbt"], list):
        raise ResponseValidationError(build_response_data_error("문제 목록 형식이 올바르지 않습니다."))

    actual_question_count = len(data["cbt"])
    if actual_question_count == 0:
        raise ResponseValidationError(build_response_data_error("생성된 문제가 없습니다. 다시 시도해주세요."))
    if actual_question_count < question_count:
        data["cbt_count_notice"] = (
            f"요청한 문제 수는 {question_count}문제였지만 "
            f"인공지능이 {actual_question_count}문제만 생성했습니다. "
            "생성된 문제로 학습을 진행합니다."
        )
    elif actual_question_count > question_count:
        data["cbt"] = data["cbt"][:question_count]
        data["cbt_count_notice"] = (
            f"인공지능이 {actual_question_count}문제를 생성했습니다. "
            f"요청한 {question_count}문제만 사용합니다."
        )

    for index, question in enumerate(data["cbt"], start=1):
        if not isinstance(question, dict):
            raise ResponseValidationError(build_response_data_error(f"{index}번 문제 형식이 올바르지 않습니다."))
        for key in ["question", "choices", "answer_index", "explanation"]:
            if key not in question:
                raise ResponseValidationError(build_response_data_error(f"{index}번 문제에 필요한 값이 없습니다."))
        if not isinstance(question["question"], str) or not question["question"].strip():
            raise ResponseValidationError(build_response_data_error(f"{index}번 문제 내용이 비어 있습니다."))
        if not isinstance(question["choices"], list) or len(question["choices"]) != 4:
            raise ResponseValidationError(build_response_data_error(f"{index}번 문제는 선택지 4개가 필요합니다."))
        if not all(isinstance(choice, str) and choice.strip() for choice in question["choices"]):
            raise ResponseValidationError(build_response_data_error(f"{index}번 선택지가 비어 있거나 문자 형식이 아닙니다."))
        normalized_choices = [normalize_choice_text(choice) for choice in question["choices"]]
        if len(set(normalized_choices)) != len(normalized_choices):
            raise ResponseValidationError(build_response_data_error(f"{index}번 문제에 중복 선택지가 있습니다."))
        answer_index = question.get("answer_index")
        if type(answer_index) is not int or answer_index not in [0, 1, 2, 3]:
            raise ResponseValidationError(build_response_data_error(f"{index}번 문제의 정답 번호가 올바르지 않습니다."))
        if not isinstance(question["explanation"], str) or not question["explanation"].strip():
            raise ResponseValidationError(build_response_data_error(f"{index}번 해설이 비어 있습니다."))


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
    st.session_state.pending_view = "My Learning"
    if clear_adaptation:
        st.session_state.adaptation_records = {}
        st.session_state.latest_adaptive_summary = None
        st.session_state.adaptation_error = None
        st.session_state.pending_recommended_difficulty = None
        st.session_state.analytics_cache = None
        st.session_state.analytics_revision = 0

def apply_pending_view() -> None:
    """Apply queued navigation before the keyed navigation widget is created."""
    pending_topic = st.session_state.pending_learning_topic
    if isinstance(pending_topic, str) and pending_topic.strip():
        st.session_state.learning_topic_input = pending_topic.strip()
    st.session_state.pending_learning_topic = None

    pending_challenge = st.session_state.pending_challenge
    if isinstance(pending_challenge, dict):
        mode = pending_challenge.get("mode")
        topic = pending_challenge.get("topic")
        if mode in world_state.CHALLENGE_MODES:
            st.session_state.challenge_mode_selector = mode
        if isinstance(topic, str) and topic.strip():
            st.session_state.challenge_topic_input = topic.strip()
        st.session_state.active_challenge_source_recommendation_id = (
            pending_challenge.get("recommendation_id", "")
        )
    st.session_state.pending_challenge = None

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
        "active_view": "My Learning",
        "pending_view": None,
        "pending_learning_topic": None,
        "pending_challenge": None,
        "active_challenge_source_recommendation_id": "",
        "world_data": None,
        "lesson_origin": "Learning",
        "learning_started_at": None,
        "active_recovery_session_id": None,
        "recovery_question_index": 0,
        "recovery_feedback": None,
        "expansion_api": None,
        BYOK_API_KEY_STATE: "",
        BYOK_CONNECTION_STATE: "missing",
        BYOK_NOTICE_STATE: None,
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
        st.session_state.active_view = "My Learning"
    if st.session_state.pending_view not in (None, *NAVIGATION_OPTIONS):
        st.session_state.pending_view = None
    if not isinstance(st.session_state.pending_learning_topic, (str, type(None))):
        st.session_state.pending_learning_topic = None
    if not isinstance(st.session_state.pending_challenge, (dict, type(None))):
        st.session_state.pending_challenge = None
    if not isinstance(
        st.session_state.active_challenge_source_recommendation_id,
        str,
    ):
        st.session_state.active_challenge_source_recommendation_id = ""
    if not isinstance(st.session_state.world_data, dict):
        st.session_state.world_data = world_state.load_world_state()
    else:
        st.session_state.world_data = world_state.normalize_world_state(
            st.session_state.world_data
        )
    if st.session_state.lesson_origin not in ("Learning", "Challenge"):
        st.session_state.lesson_origin = "Learning"
    if not isinstance(st.session_state.learning_started_at, (int, float)):
        st.session_state.learning_started_at = None
    if type(st.session_state.recovery_question_index) is not int:
        st.session_state.recovery_question_index = 0
    if not isinstance(st.session_state.recovery_feedback, (dict, type(None))):
        st.session_state.recovery_feedback = None
    active_recovery_ids = [
        item.get("id")
        for item in st.session_state.world_data["recovery_sessions"]
        if item.get("status") == "active"
    ]
    if st.session_state.active_recovery_session_id not in active_recovery_ids:
        st.session_state.active_recovery_session_id = (
            active_recovery_ids[-1]
            if active_recovery_ids
            else None
        )
    if not isinstance(st.session_state.expansion_api, ExpansionAPI):
        st.session_state.expansion_api = ExpansionAPI()
    if not normalize_api_key_input(st.session_state[BYOK_API_KEY_STATE]):
        st.session_state[BYOK_API_KEY_STATE] = ""
        st.session_state[BYOK_CONNECTION_STATE] = "missing"
    elif st.session_state[BYOK_CONNECTION_STATE] not in (
        "registered",
        "connected",
        "failed",
    ):
        st.session_state[BYOK_CONNECTION_STATE] = "registered"
    if st.session_state[BYOK_NOTICE_STATE] not in (
        None,
        "registered",
        "deleted",
    ):
        st.session_state[BYOK_NOTICE_STATE] = None


def save_world_data() -> None:
    """Persist normalized World data after an explicit learner action."""
    st.session_state.world_data = world_state.normalize_world_state(
        st.session_state.world_data
    )
    world_state.save_world_state(st.session_state.world_data)

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
    started_at = st.session_state.learning_started_at
    duration_seconds = (
        max(0, round(time.time() - started_at))
        if isinstance(started_at, (int, float))
        else 0
    )
    world_state.record_completed_round(
        st.session_state.world_data,
        lesson,
        st.session_state.answers,
        origin=st.session_state.lesson_origin,
        duration_seconds=duration_seconds,
    )
    save_world_data()

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
        f"난이도: {world_state.difficulty_label(difficulty)} | "
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
    if st.button("작성 내용 저장", key="save_learning_work"):
        direct_answer = str(st.session_state.get("direct_input", "")).strip()
        practice_answer = str(st.session_state.get("practice_input", "")).strip()
        if not direct_answer and not practice_answer:
            st.warning("저장할 작성 내용이 없습니다.")
        else:
            content = (
                f"[직접 작성 과제]\n{lesson['direct_task']}\n\n"
                f"[작성 내용]\n{direct_answer or '미작성'}\n\n"
                f"[실습]\n{lesson['practice']}\n\n"
                f"[실습 답안]\n{practice_answer or '미작성'}"
            )
            world_state.add_note(
                st.session_state.world_data,
                f"{lesson['topic']} 학습 작성 기록",
                content,
                lesson["topic"],
            )
            save_world_data()
            st.success("작성 내용을 학습 자료실 노트에 저장했습니다.")

    render_cbt(lesson)


def render_cbt(lesson: dict) -> None:
    normalize_round_state(lesson)
    questions = lesson["cbt"]
    total_questions = len(questions)
    if total_questions == 0:
        st.error("문제가 없습니다. 학습을 다시 시작해주세요.")
        return

    current_index = min(st.session_state.current_question_index, total_questions - 1)
    question = questions[current_index]

    st.subheader("문제 풀이")
    st.write(
        f"난이도: "
        f"{world_state.difficulty_label(lesson.get('difficulty', 'Easy'))}"
    )
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
    result_columns[3].metric(
        "난이도",
        world_state.difficulty_label(lesson.get("difficulty", "Easy")),
    )

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
    st.header("적응형 학습 안내")
    st.caption("현재 세션과 현재 주제의 결과만 사용한 참고용 추천입니다.")

    st.subheader("라운드 상태")
    st.write(
        f"난이도 {world_state.difficulty_label(status['difficulty'])} | "
        f"정답 {status['correct_count']} / "
        f"{status['question_count']} | 정확도 {status['accuracy']:.0f}%"
    )
    st.write(
        "보고된 확신도 — "
        f"높음 {confidence.get('high', 0)}, 보통 {confidence.get('medium', 0)}, "
        f"낮음 {confidence.get('low', 0)}, 미선택 {confidence.get('unset', 0)}"
    )

    st.subheader("학습 패턴")
    for signal in summary["learning_patterns"]:
        st.write(
            f"- {PATTERN_LABELS.get(signal['name'], '학습 신호')}: "
            f"{signal['reason']}"
        )

    st.subheader("학습 진행")
    st.write(f"이 세션에서 같은 주제로 완료한 라운드: {progress['completed_rounds']}")
    if progress["accuracy_change"] is None:
        st.write("이전 라운드가 없어 정확도 변화는 아직 계산하지 않습니다.")
    else:
        st.write(
            f"이전 라운드 대비 정확도 변화: {progress['accuracy_change']:+.0f}%p "
            f"({TREND_LABELS.get(progress['trend'], progress['trend'])})"
        )

    st.subheader("다음 난이도 추천")
    st.write(
        f"현재 {world_state.difficulty_label(difficulty['current_difficulty'])} "
        f"→ 추천 "
        f"{world_state.difficulty_label(difficulty['recommended_difficulty'])}"
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
    st.write(
        f"우선순위: {PRIORITY_LABELS.get(recovery['priority'], recovery['priority'])} "
        f"| {recovery['interval']}"
    )
    st.write(recovery["reason"])
    st.caption(recovery["advisory"])


def _format_analytics_percentage(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}%"


def _analytics_round_rows(rounds: list[dict]) -> list[dict]:
    return [
        {
            "주제": item["topic_key"],
            "라운드": item["round_id"],
            "난이도": world_state.difficulty_label(item["difficulty"]),
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
            key_label: (
                world_state.difficulty_label(item["scope_key"])
                if key_label == "난이도"
                else item["scope_key"]
            ),
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


def _render_analytics_rows(rows: list[dict]) -> None:
    """Render compact analytics rows without a native dataframe dependency."""
    if not rows:
        st.write("표시할 분석 항목이 없습니다.")
        return
    for row in rows:
        visible = [
            f"{key}: {value}"
            for key, value in row.items()
            if key != "라운드" or isinstance(value, int)
        ]
        st.write("- " + " · ".join(visible))


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
            "기존 학습 결과는 정상적으로 완료되었지만 "
            "학습 분석을 표시할 수 없습니다."
        )
        return

    latest = result["latest_round"]
    current = result["current_topic"]
    overall = result["overall"]

    st.divider()
    st.header("학습 분석")
    st.caption(
        "현재 사용 중인 화면에 남아 있는 완료 라운드만 사용한 설명형 분석입니다. "
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
            reasons = ", ".join(
                ANALYTICS_RULE_LABELS.get(rule, "분석 기준")
                for rule in item["matched_rules"]
            )
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
        _render_analytics_rows(_analytics_round_rows(current["rounds"]))
    with st.expander("주제별 분석"):
        _render_analytics_rows(
            _analytics_aggregate_rows(overall["topic_summaries"], "주제")
        )
    with st.expander("난이도별 분석"):
        _render_analytics_rows(
            _analytics_aggregate_rows(overall["difficulty_summaries"], "난이도")
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
                st.write(
                    f"- {PATTERN_LABELS.get(name, '학습 신호')}: "
                    f"{count}개 라운드"
                )
        else:
            st.write("표시할 학습 패턴 신호가 없습니다.")
        if overall["skipped_record_count"]:
            st.warning(
                f"유효하지 않은 분석 레코드 {overall['skipped_record_count']}개를 제외했습니다."
            )


def render_learning_setup(
    *,
    origin: str = "Learning",
    challenge_mode: str = "",
) -> None:
    """Render the preserved universal-topic lesson controls."""
    st.caption("새 학습 시작")
    st.subheader("학습 설정")
    ai_ready = bool(get_api_key())
    if not ai_ready:
        st.info(
            "인공지능 학습 생성을 사용하려면 관리 화면에서 본인의 연결 키를 "
            "등록해주세요. 다른 학습 영역은 계속 사용할 수 있습니다."
        )
    settings = st.session_state.world_data["management"]["settings"]
    topic = st.text_input(
        "학습할 주제를 입력하세요.",
        key=f"{origin.lower()}_topic_input",
    )
    setup_columns = st.columns(2)
    default_count = settings.get("default_question_count", 5)
    default_difficulty = settings.get("default_difficulty", "Easy")
    if challenge_mode in ("Hard", "Nightmare"):
        default_difficulty = challenge_mode
    elif challenge_mode in ("Exam", "모의고사"):
        default_difficulty = "Normal"
    question_count = setup_columns[0].selectbox(
        "문제 수를 선택하세요.",
        QUESTION_COUNT_OPTIONS,
        index=QUESTION_COUNT_OPTIONS.index(default_count),
        key=f"{origin.lower()}_question_count",
    )
    difficulty = setup_columns[1].selectbox(
        "난이도를 선택하세요.",
        DIFFICULTY_OPTIONS,
        format_func=world_state.difficulty_label,
        index=DIFFICULTY_OPTIONS.index(default_difficulty),
        key=(
            "difficulty_selector"
            if origin == "Learning"
            else "challenge_difficulty_selector"
        ),
        disabled=challenge_mode in ("Hard", "Nightmare"),
    )

    if st.button(
        "학습 시작",
        disabled=st.session_state.is_generating or not ai_ready,
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
                lesson = generate_lesson(
                    cleaned_topic, question_count, difficulty
                )
                lesson["challenge_mode"] = (
                    challenge_mode if origin == "Challenge" else ""
                )
                if origin == "Challenge":
                    source_id = (
                        st.session_state.active_challenge_source_recommendation_id
                    )
                    challenge_session = world_state.start_challenge_session(
                        st.session_state.world_data,
                        challenge_mode,
                        cleaned_topic,
                        difficulty,
                        question_count,
                        source_recovery_recommendation_id=source_id,
                    )
                    lesson["challenge_session_id"] = challenge_session["id"]
                    lesson["source_recovery_recommendation_id"] = source_id
                    st.session_state.active_challenge_source_recommendation_id = ""
                    save_world_data()
                st.session_state.lesson = lesson
                st.session_state.lesson_origin = origin
                st.session_state.learning_started_at = time.time()
                st.session_state.pending_view = origin
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


def render_recovery_world() -> None:
    st.header("회복 학습")
    pending = world_state.pending_recovery_items(st.session_state.world_data)
    st.metric("복습 대기", len(pending))
    session_id = st.session_state.active_recovery_session_id
    session = next(
        (
            item
            for item in st.session_state.world_data["recovery_sessions"]
            if item.get("id") == session_id and item.get("status") == "active"
        ),
        None,
    )

    if session is None:
        if pending:
            topics = sorted({item["topic"] for item in pending})
            st.write(f"대상 주제: {', '.join(topics)}")
            if st.button("회복 학습 시작", type="primary"):
                session = world_state.start_recovery_session(
                    st.session_state.world_data
                )
                st.session_state.active_recovery_session_id = session["id"]
                st.session_state.recovery_question_index = 0
                st.session_state.recovery_feedback = None
                save_world_data()
                st.rerun()
        else:
            st.info("복습할 오답이 없습니다. 학습 또는 도전 학습을 완료해주세요.")
    else:
        items = world_state.recovery_session_items(
            st.session_state.world_data, session
        )
        current_index = min(
            st.session_state.recovery_question_index,
            max(0, len(items) - 1),
        )
        if not items:
            st.warning("회복 학습 문제를 불러올 수 없습니다.")
        else:
            item = items[current_index]
            st.subheader(
                f"오답 복습 {current_index + 1} / {session['question_count']}"
            )
            st.write(
                f"{item['topic']} · "
                f"{world_state.difficulty_label(item['difficulty'])}"
            )
            st.markdown(f"**{item['question']}**")
            selected = st.radio(
                "복습 답을 선택하세요.",
                range(len(item["choices"])),
                format_func=lambda index: item["choices"][index],
                index=None,
                key=f"recovery_{session['id']}_{item['id']}",
                disabled=st.session_state.recovery_feedback is not None,
            )
            if st.button(
                "복습 정답 확인",
                disabled=st.session_state.recovery_feedback is not None,
            ):
                if selected is None:
                    st.warning("답을 선택해주세요.")
                else:
                    is_correct = world_state.submit_recovery_answer(
                        st.session_state.world_data,
                        session["id"],
                        item["id"],
                        selected,
                    )
                    st.session_state.recovery_feedback = {
                        "is_correct": is_correct,
                        "item_id": item["id"],
                    }
                    save_world_data()
                    st.rerun()

            feedback = st.session_state.recovery_feedback
            if isinstance(feedback, dict) and feedback.get("item_id") == item["id"]:
                if feedback["is_correct"]:
                    st.success("정답입니다. 이 오답은 회복 완료로 기록됩니다.")
                else:
                    st.error("아직 회복되지 않았습니다.")
                st.write(f"정답: {item['choices'][item['answer_index']]}")
                st.write(f"해설: {item['explanation']}")
                is_last = current_index >= len(items) - 1
                if st.button("회복 학습 완료" if is_last else "다음 복습"):
                    if is_last:
                        completed = world_state.complete_recovery_session(
                            st.session_state.world_data,
                            session["id"],
                        )
                        st.session_state.active_recovery_session_id = None
                        st.session_state.recovery_question_index = 0
                        st.session_state.recovery_feedback = None
                        save_world_data()
                        st.success(
                            f"회복 학습 완료: "
                            f"{completed['correct_count']} / "
                            f"{completed['question_count']}"
                        )
                        st.rerun()
                    else:
                        st.session_state.recovery_question_index += 1
                        st.session_state.recovery_feedback = None
                        st.rerun()

    completed_sessions = world_state.recovery_history(
        st.session_state.world_data
    )
    if completed_sessions:
        st.subheader("회복 학습 기록")
        for item in reversed(completed_sessions[-10:]):
            record = item.get("record", {})
            st.write(
                f"- {', '.join(item.get('topics', [])) or '복습'} · "
                f"{record.get('correct_count', item.get('correct_count', 0))} / "
                f"{record.get('question_count', item.get('question_count', 0))} · "
                f"{float(record.get('accuracy', 0)):.1f}% · "
                f"{int(record.get('duration_seconds', 0))}초"
            )

    recommendations = world_state.pending_recovery_recommendations(
        st.session_state.world_data
    )
    if recommendations:
        st.subheader("회복 학습 추천")
        for recommendation in reversed(recommendations[-10:]):
            st.write(
                f"{recommendation.get('topic') or '복습 주제'} · "
                f"{world_state.challenge_mode_label(recommendation['mode'])}"
            )
            st.write(recommendation["reason"])
            if st.button(
                "도전 학습으로 연결",
                key=f"open_recovery_recommendation_{recommendation['id']}",
            ):
                accepted = world_state.accept_recovery_recommendation(
                    st.session_state.world_data,
                    recommendation["id"],
                )
                st.session_state.pending_challenge = {
                    "mode": accepted["mode"],
                    "topic": accepted["topic"],
                    "recommendation_id": accepted["id"],
                }
                st.session_state.pending_view = "Challenge"
                save_world_data()
                st.rerun()


def render_challenge_world() -> None:
    st.header("도전 학습")
    mode = st.radio(
        "도전 유형",
        world_state.CHALLENGE_MODES,
        format_func=world_state.challenge_mode_label,
        horizontal=True,
        key="challenge_mode_selector",
    )
    render_learning_setup(origin="Challenge", challenge_mode=mode)
    if (
        isinstance(st.session_state.lesson, dict)
        and st.session_state.lesson_origin == "Challenge"
    ):
        st.divider()
        render_lesson(st.session_state.lesson)

    results = world_state.challenge_history(st.session_state.world_data)
    if results:
        st.subheader("도전 학습 기록")
        for result in reversed(results[-10:]):
            st.write(
                f"- {world_state.challenge_mode_label(result.get('mode', '-'))} · "
                f"{result.get('topic', '-')} · "
                f"{result.get('correct_count', 0)}/"
                f"{result.get('question_count', 0)} · "
                f"{float(result.get('accuracy', 0)):.1f}%"
            )


def _ai_context() -> str:
    stats = world_state.learning_stats(st.session_state.world_data)
    evidence = world_state.build_world_analytics(st.session_state.world_data)
    lesson = st.session_state.lesson if isinstance(st.session_state.lesson, dict) else {}
    return (
        f"현재 주제: {lesson.get('topic', '없음')}\n"
        f"학습 라운드: {evidence['learning_round_count']}\n"
        f"회복 학습: {evidence['recovery_session_count']}\n"
        f"도전 학습: {evidence['challenge_session_count']}\n"
        f"전체 정확도: {evidence['accuracy']:.1f}%\n"
        f"복습 대기 문제: {evidence['pending_recovery_count']}\n"
        f"학습 계획 목표/일정: {evidence['planner_goal_count']}/"
        f"{evidence['planner_schedule_count']}\n"
        f"학습 자료실 기록: "
        f"{evidence['library_resource_count'] + evidence['library_note_count']}\n"
        f"레벨: {stats['level']}"
    )


def generate_ai_world_text(kind: str, request: str) -> str:
    api_key = get_api_key()
    if not api_key:
        raise ConfigurationError(
            "본인의 인공지능 연결 키를 관리 화면에서 먼저 등록해주세요."
        )

    task_rules = {
        "질문": "학습자의 질문에 정확하고 이해하기 쉬운 한국어로 답하세요.",
        "해설": (
            "현재 학습 기록과 사용자의 요청을 바탕으로 개념 또는 오답 원인을 "
            "단계적으로 이해하기 쉽게 해설하세요."
        ),
        "추천": (
            "제공된 학습 기록만 근거로 다음 학습 행동을 3개 이내로 추천하세요. "
            "자동으로 일정이나 학습을 시작했다고 표현하지 마세요."
        ),
        "요약": (
            "현재 학습 맥락을 핵심 개념, 취약점, 다음 복습 항목으로 나누어 "
            "간결한 한국어로 요약하세요."
        ),
    }
    prompt = (
        f"{task_rules[kind]}\n\n[학습 맥락]\n{_ai_context()}\n\n"
        f"[사용자 요청]\n{request.strip() or kind}"
    )
    client = create_openai_client(api_key)
    try:
        response = client.responses.create(
            model=get_model(),
            input=prompt,
            temperature=0.2,
        )
    except Exception as error:
        raise ApiRequestError(build_api_error_message()) from error
    return extract_text(response).strip()


def render_ai_world() -> None:
    st.header("인공지능")
    ai_ready = bool(get_api_key())
    if not ai_ready:
        st.info(
            "인공지능 기능을 사용하려면 관리 화면에서 본인의 연결 키를 "
            "등록해주세요."
        )
        if st.button("연결 설정으로 이동"):
            st.session_state.pending_view = "Management"
            st.rerun()
    kind = st.radio(
        "인공지능 기능",
        ("질문", "해설", "추천", "요약"),
        horizontal=True,
        disabled=not ai_ready,
    )
    default_request = {
        "질문": "",
        "해설": "최근 학습 내용과 오답을 이해하기 쉽게 해설해주세요.",
        "추천": "현재 기록을 기준으로 다음 학습을 추천해주세요.",
        "요약": "현재 학습 상태를 요약해주세요.",
    }[kind]
    request = st.text_area(
        f"인공지능 {kind}",
        value=default_request,
        key=f"ai_request_{kind}",
        disabled=not ai_ready,
    )
    if st.button(
        f"인공지능 {kind} 실행",
        type="primary",
        disabled=not ai_ready,
    ):
        if kind == "질문" and not request.strip():
            st.warning("질문을 입력해주세요.")
        else:
            with st.spinner(f"인공지능 {kind}을 생성하는 중입니다."):
                try:
                    response = generate_ai_world_text(kind, request)
                    topic = (
                        st.session_state.lesson.get("topic", "")
                        if isinstance(st.session_state.lesson, dict)
                        else ""
                    )
                    world_state.add_ai_history(
                        st.session_state.world_data,
                        kind,
                        request,
                        response,
                        topic,
                    )
                    save_world_data()
                except Exception as exc:
                    st.error(user_facing_error_message(exc))
    history = st.session_state.world_data["ai_history"]
    if history:
        latest = history[-1]
        st.subheader(f"최근 인공지능 {latest['kind']}")
        st.write(latest["response"])
        link = latest.get("planner_link", {})
        if latest.get("kind") == "추천" and link.get("status") == "available":
            if st.button(
                "학습 계획 목표·일정으로 연결",
                key=f"connect_ai_planner_{latest['id']}",
            ):
                world_state.connect_ai_recommendation_to_planner(
                    st.session_state.world_data,
                    latest["id"],
                )
                st.session_state.pending_view = "Planner"
                save_world_data()
                st.rerun()
        elif latest.get("kind") == "추천" and link.get("status") == "linked":
            st.info("이 인공지능 추천은 학습 계획 목표와 일정에 연결되었습니다.")


def render_planner_world() -> None:
    st.header("학습 계획")
    st.subheader("오늘 학습")
    today_items = world_state.today_schedule(st.session_state.world_data)
    if not today_items:
        st.info("오늘 예정된 학습이 없습니다.")
    for item in today_items:
        columns = st.columns([4, 1, 1])
        columns[0].write(
            f"{item['title']} · {world_state.world_label(item['world'])}"
            + (f" · {item['topic']}" if item.get("topic") else "")
        )
        if columns[1].button("이동", key=f"open_schedule_{item['id']}"):
            if item["world"] == "Learning" and item.get("topic"):
                st.session_state.pending_learning_topic = item["topic"]
            st.session_state.pending_view = item["world"]
            st.rerun()
        if columns[2].button("완료", key=f"complete_schedule_{item['id']}"):
            world_state.set_schedule_completed(
                st.session_state.world_data,
                item["id"],
                True,
            )
            save_world_data()
            st.rerun()

    st.subheader("목표")
    goal_columns = st.columns([3, 1])
    goal_title = goal_columns[0].text_input("새 목표", key="planner_goal_title")
    goal_date = goal_columns[1].date_input(
        "목표일", value=date.today(), key="planner_goal_date"
    )
    if st.button("목표 추가"):
        try:
            world_state.add_goal(
                st.session_state.world_data,
                goal_title,
                goal_date.isoformat(),
            )
            save_world_data()
            st.rerun()
        except ValueError as exc:
            st.warning(str(exc))
    for goal in reversed(st.session_state.world_data["planner"]["goals"][-20:]):
        columns = st.columns([5, 1])
        status = "완료" if goal.get("completed") else "진행 중"
        columns[0].write(
            f"{goal['title']} · {goal.get('target_date') or '기한 없음'} · {status}"
        )
        if columns[1].button(
            "다시 열기" if goal.get("completed") else "완료",
            key=f"toggle_goal_{goal['id']}",
        ):
            world_state.set_goal_completed(
                st.session_state.world_data,
                goal["id"],
                not goal.get("completed"),
            )
            save_world_data()
            st.rerun()

    st.subheader("일정")
    schedule_columns = st.columns(3)
    schedule_title = schedule_columns[0].text_input(
        "일정 제목", key="planner_schedule_title"
    )
    schedule_date = schedule_columns[1].date_input(
        "학습일", value=date.today(), key="planner_schedule_date"
    )
    schedule_world = schedule_columns[2].selectbox(
        "연결 학습 영역",
        world_state.WORLD_NAMES,
        format_func=world_state.world_label,
        key="planner_schedule_world",
    )
    schedule_topic = st.text_input("연결 주제 (선택)", key="planner_schedule_topic")
    if st.button("일정 추가"):
        try:
            world_state.add_schedule(
                st.session_state.world_data,
                schedule_title,
                schedule_date.isoformat(),
                schedule_world,
                schedule_topic,
            )
            save_world_data()
            st.rerun()
        except ValueError as exc:
            st.warning(str(exc))


def render_library_world() -> None:
    st.header("학습 자료실")
    query = st.text_input("자료와 노트 검색", key="library_search_query")
    if query.strip():
        results = world_state.search_library(st.session_state.world_data, query)
        st.subheader(f"검색 결과 {len(results)}개")
        for item in results:
            with st.expander(
                f"{world_state.resource_kind_label(item['kind'])} · "
                f"{localize_system_text(item.get('title', '자료'))}"
            ):
                if item["kind"] == "노트":
                    st.write(item.get("content", ""))
                else:
                    st.caption(
                        f"{world_state.world_label(item.get('source_world', 'Learning'))} "
                        f"· {world_state.resource_kind_label(item.get('kind', '자료'))}"
                    )
                    st.write(
                        item.get("content")
                        or item.get("tutorial", "")
                        or item.get("example", "")
                    )

    st.subheader("노트")
    note_title = st.text_input("노트 제목", key="library_note_title")
    note_topic = st.text_input("노트 주제", key="library_note_topic")
    note_content = st.text_area("노트 내용", key="library_note_content")
    if st.button("노트 저장"):
        try:
            world_state.add_note(
                st.session_state.world_data,
                note_title,
                note_content,
                note_topic,
            )
            save_world_data()
            st.rerun()
        except ValueError as exc:
            st.warning(str(exc))
    for note in reversed(st.session_state.world_data["library"]["notes"][-10:]):
        with st.expander(f"{note['title']} · {note.get('topic') or '주제 없음'}"):
            st.write(note["content"])

    st.subheader("자료실")
    resources = st.session_state.world_data["library"]["resources"]
    if not resources:
        st.info("완료한 학습의 자료가 여기에 자동으로 보관됩니다.")
    for resource in reversed(resources[-10:]):
        with st.expander(localize_system_text(resource["title"])):
            st.caption(
                f"{world_state.world_label(resource.get('source_world', 'Learning'))} "
                f"· {world_state.resource_kind_label(resource.get('kind', '자료'))}"
            )
            details = resource.get("details", {})
            if isinstance(details, dict) and details.get("tutorial"):
                st.markdown("**개념 설명**")
                st.write(details["tutorial"])
                st.markdown("**예제**")
                st.write(details.get("example", ""))
                st.markdown("**직접 과제 / 실습**")
                st.write(details.get("direct_task", ""))
                st.write(details.get("practice", ""))
            elif resource.get("tutorial"):
                st.markdown("**개념 설명**")
                st.write(resource.get("tutorial", ""))
                st.markdown("**예제**")
                st.write(resource.get("example", ""))
                st.markdown("**직접 과제 / 실습**")
                st.write(resource.get("direct_task", ""))
                st.write(resource.get("practice", ""))
            else:
                content = resource.get("content", "")
                if resource.get("source_world") in (
                    "Recovery",
                    "Challenge",
                    "Planner",
                ):
                    content = localize_system_text(content)
                st.write(content)


def reset_transient_learning_state(*, next_view: str = "Management") -> None:
    """Clear session-only views after durable records have been removed."""
    reset_learning_state(clear_adaptation=True)
    st.session_state.lesson_origin = "Learning"
    st.session_state.learning_started_at = None
    st.session_state.active_recovery_session_id = None
    st.session_state.recovery_question_index = 0
    st.session_state.recovery_feedback = None
    st.session_state.pending_learning_topic = None
    st.session_state.pending_challenge = None
    st.session_state.active_challenge_source_recommendation_id = ""
    st.session_state.pending_view = next_view


def render_user_data_management() -> None:
    st.subheader("사용자 데이터 관리")
    st.caption(
        "삭제한 기록은 복구할 수 없습니다. 필요한 경우 먼저 백업을 내려받으세요."
    )
    catalog = world_state.deletion_catalog(st.session_state.world_data)
    labels = {item["token"]: item["label"] for item in catalog}
    tokens = [item["token"] for item in catalog]

    with st.expander("선택 삭제"):
        selected_tokens = st.multiselect(
            "삭제할 기록",
            tokens,
            format_func=lambda token: labels.get(token, "기록"),
            key="data_delete_selected_records",
            help="여러 기록을 선택할 수 있습니다. 연결된 자동 생성 자료도 함께 정리됩니다.",
        )
        selected_confirmed = st.checkbox(
            "선택한 기록이 삭제되는 것에 동의합니다.",
            key="data_delete_selected_confirm",
        )
        if st.button(
            "선택한 기록 삭제",
            disabled=not selected_tokens or not selected_confirmed,
            key="data_delete_selected_button",
        ):
            deleted = world_state.delete_selected_records(
                st.session_state.world_data,
                selected_tokens,
            )
            save_world_data()
            reset_transient_learning_state()
            st.success(f"선택한 기록 {deleted}개를 삭제했습니다.")

    with st.expander("종류별 기록 삭제"):
        category = st.selectbox(
            "삭제할 기록 종류",
            tuple(world_state.RECORD_CATEGORY_LABELS),
            format_func=lambda value: world_state.RECORD_CATEGORY_LABELS[value],
            key="data_delete_category",
        )
        category_count = sum(
            item["category"] == category for item in catalog
        )
        st.caption(f"현재 {category_count}개 기록이 있습니다.")
        category_confirmed = st.checkbox(
            "이 종류의 기록을 모두 삭제하는 것에 동의합니다.",
            key="data_delete_category_confirm",
        )
        if st.button(
            "이 종류의 기록 모두 삭제",
            disabled=not category_count or not category_confirmed,
            key="data_delete_category_button",
        ):
            deleted = world_state.clear_record_category(
                st.session_state.world_data,
                category,
            )
            save_world_data()
            reset_transient_learning_state()
            st.success(f"{world_state.RECORD_CATEGORY_LABELS[category]} {deleted}개를 삭제했습니다.")

    with st.expander("전체 기록 삭제"):
        st.write("학습 기록과 연결 자료를 모두 삭제합니다. 과목과 기본 설정은 유지됩니다.")
        all_confirmation = st.text_input(
            "확인을 위해 ‘전체 삭제’를 입력하세요.",
            key="data_delete_all_confirmation",
        )
        if st.button(
            "모든 학습 기록 삭제",
            disabled=all_confirmation.strip() != "전체 삭제",
            key="data_delete_all_button",
        ):
            deleted = world_state.clear_all_records(st.session_state.world_data)
            save_world_data()
            reset_transient_learning_state()
            st.success(f"학습 기록 {deleted}개를 삭제했습니다. 과목과 기본 설정은 유지됩니다.")

    with st.expander("앱 데이터 초기화"):
        st.write(
            "모든 기록, 과목, 기본 설정과 현재 인공지능 연결 키를 초기화합니다."
        )
        reset_confirmation = st.text_input(
            "확인을 위해 ‘초기화’를 입력하세요.",
            key="data_reset_confirmation",
        )
        if st.button(
            "모든 사용자 데이터 초기화",
            disabled=reset_confirmation.strip() != "초기화",
            key="data_reset_button",
        ):
            deleted = world_state.reset_user_data(st.session_state.world_data)
            delete_api_key()
            save_world_data()
            reset_transient_learning_state(next_view="My Learning")
            st.success(f"사용자 데이터를 초기화했습니다. 정리된 기록: {deleted}개")


def render_management_world() -> None:
    st.header("관리")
    st.subheader("확장 기능")
    statuses = st.session_state.expansion_api.list()
    if not statuses:
        st.info("설치된 확장 기능이 없습니다.")
    for status in statuses:
        st.write(
            f"- {status.name} {status.version} · "
            f"{'로드됨' if status.loaded else '설치됨'}"
        )

    st.subheader("인공지능 연결")
    st.write(
        "본인의 오픈에이아이 계정에서 발급한 연결 키를 등록하면 "
        "인공지능 학습 기능을 사용할 수 있습니다."
    )
    registered_key = get_api_key()
    connection_status = st.session_state[BYOK_CONNECTION_STATE]
    notice = st.session_state.pop(BYOK_NOTICE_STATE, None)
    if notice == "registered":
        st.success("인공지능 연결 키가 현재 이용 중인 화면에 등록되었습니다.")
    elif notice == "deleted":
        st.success("현재 이용 중인 화면의 인공지능 연결 키를 삭제했습니다.")
    if not registered_key:
        st.info("등록된 연결 키가 없습니다. 인공지능 기능만 비활성화됩니다.")
    elif connection_status == "connected":
        st.success("인공지능 서비스 연결이 확인되었습니다.")
    elif connection_status == "failed":
        st.warning("인공지능 서비스 연결을 확인할 수 없습니다.")
    else:
        st.info("인공지능 연결 키가 등록되어 있습니다. 연결 확인을 실행해주세요.")
    st.caption(
        "연결 키는 현재 브라우저 이용 시간 동안 서버 메모리에만 보관되며 "
        "저장 파일, 백업, 코드 저장소, 로그에 포함되지 않습니다."
    )
    with st.form("byok_api_key_form", clear_on_submit=True):
        api_key_input = st.text_input(
            "인공지능 연결 키",
            type="password",
            help="앞뒤 공백 없이 발급받은 키 전체를 입력하세요.",
        )
        submitted = st.form_submit_button(
            "연결 키 변경" if registered_key else "연결 키 등록"
        )
    if submitted:
        try:
            register_api_key(api_key_input)
            st.session_state[BYOK_NOTICE_STATE] = "registered"
            st.rerun()
        except ConfigurationError as error:
            st.warning(user_facing_error_message(error))

    api_columns = st.columns(2)
    if api_columns[0].button(
        "연결 확인",
        disabled=not bool(registered_key),
        use_container_width=True,
    ):
        try:
            test_openai_connection(registered_key or "")
            st.session_state[BYOK_CONNECTION_STATE] = "connected"
            st.success("인공지능 서비스 연결이 정상입니다.")
        except Exception as error:
            st.session_state[BYOK_CONNECTION_STATE] = "failed"
            st.error(user_facing_error_message(error))
    key_delete_confirmed = st.checkbox(
        "연결 키 삭제에 동의합니다.",
        key="byok_delete_confirm",
        disabled=not bool(registered_key),
    )
    if api_columns[1].button(
        "연결 키 삭제",
        disabled=not bool(registered_key) or not key_delete_confirmed,
        use_container_width=True,
    ):
        delete_api_key()
        st.session_state[BYOK_NOTICE_STATE] = "deleted"
        st.rerun()

    st.subheader("과목 관리")
    new_subject = st.text_input("과목 추가", key="management_new_subject")
    if st.button("과목 저장"):
        cleaned = new_subject.strip()[:80]
        if not cleaned:
            st.warning("과목명을 입력해주세요.")
        elif cleaned in st.session_state.world_data["management"]["subjects"]:
            st.info("이미 등록된 과목입니다.")
        else:
            st.session_state.world_data["management"]["subjects"].append(cleaned)
            st.session_state.world_data["management"]["subjects"].sort(
                key=str.casefold
            )
            world_state.add_activity(
                st.session_state.world_data,
                "Management",
                "과목 등록",
                topic=cleaned,
            )
            save_world_data()
            st.rerun()
    subjects = st.session_state.world_data["management"]["subjects"]
    if subjects:
        remove_subject = st.selectbox(
            "등록 과목", subjects, key="management_subject_remove"
        )
        if st.button("선택 과목 제거"):
            subjects.remove(remove_subject)
            world_state.add_activity(
                st.session_state.world_data,
                "Management",
                "과목 제거",
                topic=remove_subject,
            )
            save_world_data()
            st.rerun()

    st.subheader("설정")
    settings = st.session_state.world_data["management"]["settings"]
    setting_columns = st.columns(2)
    default_count = setting_columns[0].selectbox(
        "기본 문제 수",
        QUESTION_COUNT_OPTIONS,
        index=QUESTION_COUNT_OPTIONS.index(settings["default_question_count"]),
        key="management_default_count",
    )
    default_difficulty = setting_columns[1].selectbox(
        "기본 난이도",
        DIFFICULTY_OPTIONS,
        format_func=world_state.difficulty_label,
        index=DIFFICULTY_OPTIONS.index(settings["default_difficulty"]),
        key="management_default_difficulty",
    )
    if st.button("설정 저장"):
        settings["default_question_count"] = default_count
        settings["default_difficulty"] = default_difficulty
        world_state.add_activity(
            st.session_state.world_data, "Management", "학습 설정 변경"
        )
        save_world_data()
        st.success("설정을 저장했습니다.")

    st.subheader("백업")
    backup_text = world_state.export_world_state(st.session_state.world_data)
    st.download_button(
        "백업 다운로드",
        data=backup_text,
        file_name="통합학습엔진-백업.ule",
        mime="application/octet-stream",
    )
    uploaded = st.file_uploader(
        "백업 파일 선택",
        key="management_backup_file",
        help="이 앱에서 내려받은 백업 파일을 선택하세요.",
    )
    if st.button("백업 복원"):
        if uploaded is None:
            st.warning("복원할 백업 파일을 선택해주세요.")
        else:
            try:
                restored = world_state.import_world_state(
                    uploaded.getvalue().decode("utf-8")
                )
                st.session_state.world_data = restored
                save_world_data()
                st.success("백업을 복원했습니다.")
                st.rerun()
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                LOGGER.warning(
                    "backup_restore_failed error_type=%s",
                    type(exc).__name__,
                )
                st.error(
                    "백업 파일을 확인할 수 없습니다. "
                    "이 앱에서 내려받은 파일인지 확인해주세요."
                )

    render_user_data_management()


def render_analytics_world() -> None:
    st.header("학습 분석")
    evidence = world_state.build_world_analytics(st.session_state.world_data)
    columns = st.columns(4)
    columns[0].metric(
        "학습",
        evidence["learning_round_count"],
    )
    columns[1].metric(
        "회복 학습",
        evidence["recovery_session_count"],
    )
    columns[2].metric(
        "도전 학습",
        evidence["challenge_session_count"],
    )
    columns[3].metric("전체 정확도", f"{evidence['accuracy']:.1f}%")
    lesson = st.session_state.lesson
    if isinstance(lesson, dict) and st.session_state.round_finished:
        render_learning_analytics(lesson)
    elif not evidence["question_count"]:
        st.info("분석할 학습 기록이 없습니다.")
    st.subheader("도전 학습 분석")
    for mode, item in evidence["challenge_modes"].items():
        st.write(
            f"- {world_state.challenge_mode_label(mode)}: "
            f"{item['session_count']}회 · "
            f"{item['question_count']}문항 · {item['accuracy']:.1f}%"
        )
    st.subheader("학습 영역 연결 통계")
    st.write(
        f"인공지능 {evidence['ai_count']}건 · "
        f"학습 계획 목표 {evidence['planner_goal_count']}개 · "
        f"학습 계획 일정 {evidence['planner_schedule_count']}개 · "
        f"학습 자료실 자료 {evidence['library_resource_count']}개 · "
        f"노트 {evidence['library_note_count']}개"
    )
    report = world_state.build_report(st.session_state.world_data)
    st.subheader("학습 보고서")
    st.download_button(
        "학습 리포트 다운로드",
        data=report,
        file_name="학습-보고서.md",
        mime="text/markdown",
    )
    with st.expander("리포트 미리보기"):
        st.markdown(report)


def render_my_learning_world() -> None:
    st.header("나의 학습")
    stats = world_state.learning_stats(st.session_state.world_data)
    challenge_count = stats.get(
        "challenge_count",
        stats.get("world_records", {}).get("Challenge", 0),
    )
    columns = st.columns(4)
    columns[0].metric("공부시간", f"{stats['study_seconds'] // 60}분")
    columns[1].metric("레벨", stats["level"])
    columns[2].metric("완료 라운드", stats["round_count"])
    columns[3].metric("전체 정확도", f"{stats['accuracy']:.1f}%")
    st.progress((stats["points"] % 100) / 100)
    st.caption(f"다음 레벨까지 {100 - (stats['points'] % 100)} 포인트")

    st.subheader("업적")
    if stats["achievements"]:
        for achievement in stats["achievements"]:
            st.write(f"- {achievement}")
    else:
        st.info("첫 학습을 완료하면 업적이 시작됩니다.")

    st.subheader("장기 통계")
    st.write(
        f"학습 주제 {stats['topic_count']}개 · "
        f"분석 문항 {stats['question_count']}개 · "
        f"회복 학습 {stats['recovery_count']}회 · "
        f"도전 학습 {challenge_count}회"
    )
    st.write(
        f"인공지능 {stats['ai_count']}건 · "
        f"학습 계획 목표/일정 {stats['planner_goal_count']}/"
        f"{stats['planner_schedule_count']}개 · "
        f"학습 자료실 {stats['library_count']}개 · "
        f"관리 과목 {stats['subject_count']}개"
    )
    st.subheader("학습 영역별 기록")
    for world in world_state.WORLD_NAMES:
        st.write(
            f"- {world_state.world_label(world)}: "
            f"{stats['world_records'].get(world, 0)}"
        )
    st.subheader("최근 활동")
    activity = st.session_state.world_data["activity"]
    if not activity:
        st.info("기록된 활동이 없습니다.")
    for item in reversed(activity[-10:]):
        st.write(
            f"- {world_state.world_label(item.get('world', '-'))} · "
            f"{localize_system_text(item.get('action', '-'))}"
            + (f" · {item['topic']}" if item.get("topic") else "")
        )


def main() -> None:
    configure_logging()
    st.set_page_config(
        page_title=f"{APP_TITLE} v1.06",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_state()
    apply_pending_difficulty_recommendation()
    apply_pending_view()

    apply_official_theme(st)
    st.title(APP_TITLE)
    st.write(APP_DESCRIPTION)
    selected_view = render_navigation(st)
    st.divider()

    if selected_view == "Learning":
        st.header("학습")
        render_learning_setup()
        if (
            isinstance(st.session_state.lesson, dict)
            and st.session_state.lesson_origin == "Learning"
        ):
            st.divider()
            render_lesson(st.session_state.lesson)
    elif selected_view == "Recovery":
        render_recovery_world()
    elif selected_view == "Challenge":
        render_challenge_world()
    elif selected_view == "Analytics":
        render_analytics_world()
    elif selected_view == "AI":
        render_ai_world()
    elif selected_view == "Planner":
        render_planner_world()
    elif selected_view == "Library":
        render_library_world()
    elif selected_view == "Management":
        render_management_world()
    else:
        render_my_learning_world()


if __name__ == "__main__":
    main()
