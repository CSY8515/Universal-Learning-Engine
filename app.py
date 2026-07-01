import json
import os

import streamlit as st


APP_TITLE = "Universal Learning Engine"
APP_DESCRIPTION = "학습할 주제를 입력하면 동일한 학습 엔진이 해당 주제에 맞게 동작합니다."
DEFAULT_MODEL = "gpt-4.1-mini"


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


def build_prompt(topic: str) -> str:
    return f"""
너는 Universal Learning Engine v0.1이다.

목표:
입력된 학습 주제 하나를 대상으로 가장 작은 MVP 학습 Flow를 생성한다.

학습 주제:
{topic}

규칙:
- 주제별 하드코딩 없이 입력 주제에 맞게 일반적으로 설명한다.
- 확장 기능을 만들지 않는다.
- 난이도 조절, 분석, 추천, 복습 스케줄, 대시보드 내용을 넣지 않는다.
- CBT는 반드시 5문제만 만든다.
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
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    return json.loads(cleaned)


def generate_lesson(topic: str) -> dict:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다. 로컬에서는 .env, Streamlit Cloud에서는 Secrets를 설정해주세요.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai 패키지가 설치되어 있지 않습니다. requirements.txt를 설치해주세요.") from exc

    client = OpenAI(api_key=api_key)
    model = get_model()
    prompt = build_prompt(topic)

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=0.2,
        )
    except Exception:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

    data = parse_json_response(extract_text(response))
    validate_lesson(data)
    return data


def validate_lesson(data: dict) -> None:
    required_keys = ["topic", "tutorial", "example", "direct_task", "practice", "cbt"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"응답에 필요한 값이 없습니다: {key}")

    if not isinstance(data["cbt"], list) or len(data["cbt"]) != 5:
        raise ValueError("CBT 문제는 반드시 5문제여야 합니다.")

    for index, question in enumerate(data["cbt"], start=1):
        if len(question.get("choices", [])) != 4:
            raise ValueError(f"CBT {index}번 문제는 선택지 4개가 필요합니다.")
        answer_index = question.get("answer_index")
        if not isinstance(answer_index, int) or answer_index not in [0, 1, 2, 3]:
            raise ValueError(f"CBT {index}번 문제의 정답 번호가 올바르지 않습니다.")


def reset_learning_state() -> None:
    st.session_state.lesson = None
    st.session_state.answers = {}
    st.session_state.submitted = False


def init_state() -> None:
    if "lesson" not in st.session_state:
        st.session_state.lesson = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "submitted" not in st.session_state:
        st.session_state.submitted = False


def render_lesson(lesson: dict) -> None:
    st.header(f"학습 주제: {lesson['topic']}")

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
    st.subheader("CBT")

    for index, question in enumerate(lesson["cbt"]):
        st.markdown(f"**문제 {index + 1}. {question['question']}**")
        choice = st.radio(
            "답을 선택하세요.",
            question["choices"],
            key=f"cbt_{index}",
            index=None,
        )
        if choice is not None:
            st.session_state.answers[index] = question["choices"].index(choice)

    if st.button("제출 후 채점"):
        if len(st.session_state.answers) < 5:
            st.warning("CBT 5문제의 답을 모두 선택해주세요.")
        else:
            st.session_state.submitted = True

    if st.session_state.submitted:
        render_results(lesson)


def render_results(lesson: dict) -> None:
    wrong_answers = []

    for index, question in enumerate(lesson["cbt"]):
        user_answer = st.session_state.answers.get(index)
        if user_answer != question["answer_index"]:
            wrong_answers.append((index, question, user_answer))

    st.subheader("오답노트")
    if not wrong_answers:
        st.success("틀린 문제가 없습니다.")
    else:
        for index, question, user_answer in wrong_answers:
            st.markdown(f"**문제 {index + 1}. {question['question']}**")
            st.write(f"사용자 답: {question['choices'][user_answer]}")
            st.write(f"정답: {question['choices'][question['answer_index']]}")

    st.subheader("해설")
    for index, question in enumerate(lesson["cbt"]):
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

    if st.button("학습 시작"):
        if not topic.strip():
            st.warning("학습할 주제를 입력해주세요.")
        else:
            reset_learning_state()
            with st.spinner("학습 내용을 생성하는 중입니다."):
                try:
                    st.session_state.lesson = generate_lesson(topic.strip())
                except Exception as exc:
                    st.error(str(exc))

    if st.session_state.lesson:
        render_lesson(st.session_state.lesson)


if __name__ == "__main__":
    main()
