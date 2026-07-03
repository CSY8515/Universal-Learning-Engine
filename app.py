import json
import os

import streamlit as st


APP_TITLE = "Universal Learning Engine"
APP_DESCRIPTION = "학습할 주제를 입력하면 동일한 학습 엔진이 해당 주제에 맞게 동작합니다."
DEFAULT_MODEL = "gpt-4.1-mini"
MAX_TOPIC_LENGTH = 80
QUESTION_COUNT_OPTIONS = [5, 10, 15, 20]
DIFFICULTY_OPTIONS = ["입문", "초급", "중급"]
AI_RESPONSE_FORMAT_ERROR = "AI 응답 형식 오류입니다. 다시 시도해주세요."
AI_RESPONSE_DATA_ERROR = "AI 응답 데이터가 예상과 다릅니다. 다시 시도해주세요."


def load_local_env() -> None:
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


def get_secret_value(key: str) -> str | None:
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


def get_difficulty_rules(difficulty: str) -> str:
    rules = {
        "입문": """
입문 난이도 기준:
- 기본 용어를 묻는다.
- 단순 개념을 확인한다.
- 암기형 문제를 포함한다.
- 완전 초보자도 풀 수 있는 수준으로 만든다.
- 선택지는 너무 꼬지 말고 명확하게 만든다.
""",
        "초급": """
초급 난이도 기준:
- 기본 개념과 간단한 적용을 함께 묻는다.
- 쉬운 사례 문제를 포함한다.
- 기초 이해 여부를 확인한다.
- 단순 암기만 묻지 말고, 쉬운 상황 판단을 1~2문제 포함한다.
""",
        "중급": """
중급 난이도 기준:
- 응용 문제를 포함한다.
- 사례 기반 문제를 포함한다.
- 혼동하기 쉬운 개념 비교 문제를 포함한다.
- 실무형 또는 시험형 판단 문제를 포함한다.
- 너무 쉬운 정의형 문제는 금지한다.
- 정의만 묻는 초급 문제를 출제하지 말 것.
- 응용·사례·비교·판단형 문제를 포함할 것.

중급 주제별 예시 기준:
- 투자: "투자의 목적은?" 같은 단순 정의 문제 금지. ETF, 분산투자, 금리, 채권, 리스크, 장기투자 판단 문제를 포함한다.
- 제과제빵: "이스트 역할은?" 같은 단순 정의 문제 금지. 글루텐, 발효, 온도, 믹싱, 반죽 상태, 기능사 시험형 문제를 포함한다.
- 영어: 알파벳 개수 같은 문제 금지. 문법, 시제, 어순, 독해, 문장 수정 문제를 포함한다.
""",
    }
    return rules.get(difficulty, rules["입문"])


def build_prompt(topic: str, question_count: int, difficulty: str) -> str:
    difficulty_rules = get_difficulty_rules(difficulty)
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
        return response.output_text

    if hasattr(response, "choices"):
        return response.choices[0].message.content

    return str(response)


def parse_json_response(text: str) -> dict:
    cleaned = str(text).strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        json_start = cleaned.find("{")
        json_end = cleaned.rfind("}")
        if json_start != -1 and json_end != -1 and json_start < json_end:
            try:
                return json.loads(cleaned[json_start : json_end + 1])
            except json.JSONDecodeError:
                pass
        raise ValueError(f"{AI_RESPONSE_FORMAT_ERROR} 원인: {exc}") from exc


def build_api_error_message(error: Exception) -> str:
    return (
        "OpenAI API 호출에 실패했습니다. "
        "API 키, 결제 상태, 모델 이름, 네트워크 연결을 확인해주세요. "
        f"원인: {error}"
    )


def build_response_data_error(reason: str) -> str:
    return f"{AI_RESPONSE_DATA_ERROR} 원인: {reason}"


def generate_lesson(topic: str, question_count: int, difficulty: str) -> dict:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다. 로컬에서는 .env, Streamlit Cloud에서는 Secrets를 설정해주세요.")
    if difficulty not in DIFFICULTY_OPTIONS:
        raise ValueError(build_response_data_error("지원하지 않는 난이도입니다."))

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. requirements.txt를 설치해주세요.") from exc

    client = OpenAI(api_key=api_key)
    model = get_model()
    prompt = build_prompt(topic, question_count, difficulty)

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=0.2,
        )
    except Exception as first_error:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
        except Exception as second_error:
            raise RuntimeError(build_api_error_message(second_error)) from first_error

    data = parse_json_response(extract_text(response))
    validate_lesson(data, question_count)
    data["difficulty"] = difficulty
    data["requested_question_count"] = question_count
    return data


def validate_lesson(data: dict, question_count: int) -> None:
    if question_count not in QUESTION_COUNT_OPTIONS:
        raise ValueError(build_response_data_error("지원하지 않는 CBT 문제 수입니다."))
    if not isinstance(data, dict):
        raise ValueError(build_response_data_error("응답이 객체 형식이 아닙니다."))

    required_keys = ["topic", "tutorial", "example", "direct_task", "practice", "cbt"]
    for key in required_keys:
        if key not in data:
            raise ValueError(build_response_data_error(f"필요한 값이 없습니다({key})."))

    text_keys = ["topic", "tutorial", "example", "direct_task", "practice"]
    for key in text_keys:
        if not isinstance(data[key], str) or not data[key].strip():
            raise ValueError(build_response_data_error(f"{key} 값이 비어 있거나 문자 형식이 아닙니다."))

    if not isinstance(data["cbt"], list):
        raise ValueError(build_response_data_error("CBT 문제가 배열 형식이 아닙니다."))

    actual_question_count = len(data["cbt"])
    if actual_question_count == 0:
        raise ValueError(build_response_data_error("생성된 CBT 문제가 없습니다. 다시 시도해주세요."))
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
            raise ValueError(build_response_data_error(f"CBT {index}번 문제가 객체 형식이 아닙니다."))
        for key in ["question", "choices", "answer_index", "explanation"]:
            if key not in question:
                raise ValueError(build_response_data_error(f"CBT {index}번 문제에 {key} 값이 없습니다."))
        if not isinstance(question["question"], str) or not question["question"].strip():
            raise ValueError(build_response_data_error(f"CBT {index}번 문제 내용이 비어 있습니다."))
        if not isinstance(question["choices"], list) or len(question["choices"]) != 4:
            raise ValueError(build_response_data_error(f"CBT {index}번 문제는 선택지 4개가 필요합니다."))
        if not all(isinstance(choice, str) and choice.strip() for choice in question["choices"]):
            raise ValueError(build_response_data_error(f"CBT {index}번 선택지가 비어 있거나 문자 형식이 아닙니다."))
        answer_index = question.get("answer_index")
        if not isinstance(answer_index, int) or answer_index not in [0, 1, 2, 3]:
            raise ValueError(build_response_data_error(f"CBT {index}번 문제의 정답 번호가 올바르지 않습니다."))
        if not isinstance(question["explanation"], str) or not question["explanation"].strip():
            raise ValueError(build_response_data_error(f"CBT {index}번 해설이 비어 있습니다."))


def validate_topic_input(topic: str) -> tuple[bool, str, str]:
    cleaned_topic = topic.strip()
    if not cleaned_topic:
        return False, "", "학습할 주제를 입력해주세요."
    if len(cleaned_topic) > MAX_TOPIC_LENGTH:
        return False, "", f"학습 주제는 {MAX_TOPIC_LENGTH}자 이하로 입력해주세요."
    return True, cleaned_topic, ""


def reset_round_state() -> None:
    st.session_state.answers = {}
    st.session_state.current_question_index = 0
    st.session_state.current_feedback = None
    st.session_state.round_finished = False
    current_round_id = st.session_state.get("cbt_round_id", 0)
    st.session_state.cbt_round_id = current_round_id + 1
    for key in list(st.session_state.keys()):
        if key.startswith("cbt_") and key != "cbt_round_id":
            del st.session_state[key]


def reset_learning_state() -> None:
    st.session_state.lesson = None
    reset_round_state()


def init_state() -> None:
    if "lesson" not in st.session_state:
        st.session_state.lesson = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0
    if "current_feedback" not in st.session_state:
        st.session_state.current_feedback = None
    if "round_finished" not in st.session_state:
        st.session_state.round_finished = False
    if "cbt_round_id" not in st.session_state:
        st.session_state.cbt_round_id = 0


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
        if isinstance(key, int) and 0 <= key < total_questions and value in [0, 1, 2, 3]:
            safe_answers[key] = value
    st.session_state.answers = safe_answers

    if not isinstance(st.session_state.current_question_index, int):
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
        not isinstance(feedback_index, int)
        or feedback_index < 0
        or feedback_index >= total_questions
        or selected_index not in [0, 1, 2, 3]
        or not isinstance(feedback.get("is_correct"), bool)
    ):
        st.session_state.current_feedback = None


def render_learning_status(lesson: dict) -> None:
    topic = lesson.get("topic", "학습 주제")
    difficulty = lesson.get("difficulty", "입문")
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
    st.write(f"난이도: {lesson.get('difficulty', '입문')}")
    progress_current = total_questions if st.session_state.round_finished else current_index + 1
    st.write(f"진행률: {progress_current} / {total_questions}")
    st.progress(progress_current / total_questions)

    if st.session_state.round_finished:
        render_round_summary(lesson)
        if st.button("다시 학습"):
            reset_round_state()
            st.rerun()
        if st.button("처음으로"):
            reset_learning_state()
            st.rerun()
        return

    st.markdown(f"**문제 {current_index + 1} / {total_questions}. {question['question']}**")
    choice = st.radio(
        "답을 선택하세요.",
        question["choices"],
        key=f"cbt_{st.session_state.cbt_round_id}_{current_index}",
        index=None,
    )

    if st.button("정답 확인"):
        if choice is None:
            st.warning("답을 선택해주세요.")
        else:
            selected_index = question["choices"].index(choice)
            is_correct = selected_index == question["answer_index"]
            st.session_state.answers[current_index] = selected_index
            st.session_state.current_feedback = {
                "index": current_index,
                "is_correct": is_correct,
                "selected_index": selected_index,
            }

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
    st.write(f"난이도: {lesson.get('difficulty', '입문')}")
    st.write(f"총 문제 수: {total_questions}")
    st.write(f"정답 수: {correct_count}")
    st.write(f"오답 수: {wrong_count}")
    st.write(f"정답률: {accuracy}%")

    st.subheader("오답노트")
    if not wrong_answers:
        st.success("틀린 문제가 없습니다.")
    else:
        for index, question, user_answer in wrong_answers:
            st.markdown(f"**문제 {index + 1}. {question['question']}**")
            if user_answer is None:
                st.write("사용자 답: 미응답")
            else:
                st.write(f"사용자 답: {question['choices'][user_answer]}")
            st.write(f"정답: {question['choices'][question['answer_index']]}")

    st.subheader("해설")
    for index, question in enumerate(questions):
        st.markdown(f"**문제 {index + 1}. {question['question']}**")
        st.write(f"정답: {question['choices'][question['answer_index']]}")
        st.write(question["explanation"])

    st.subheader("학습 종료")
    st.success("학습이 완료되었습니다.")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="📘")
    init_state()

    st.title(APP_TITLE)
    st.write(APP_DESCRIPTION)

    topic = st.text_input("학습할 주제를 입력하세요.", placeholder="예: 제과제빵, Python, 영어, 투자, 역사")
    question_count = st.selectbox("CBT 문제 수를 선택하세요.", QUESTION_COUNT_OPTIONS, index=0)
    difficulty = st.selectbox("난이도를 선택하세요.", DIFFICULTY_OPTIONS, index=0)

    if st.button("학습 시작"):
        is_valid, cleaned_topic, message = validate_topic_input(topic)
        if not is_valid:
            st.warning(message)
        else:
            reset_learning_state()
            with st.spinner("학습 내용을 생성하는 중입니다."):
                try:
                    st.session_state.lesson = generate_lesson(cleaned_topic, question_count, difficulty)
                except Exception as exc:
                    st.error(str(exc))

    if st.session_state.lesson:
        render_lesson(st.session_state.lesson)


if __name__ == "__main__":
    main()
