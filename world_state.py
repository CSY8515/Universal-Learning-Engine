"""Serializable v1.02 World state and deterministic cross-World operations."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import threading
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable


WORLD_NAMES = (
    "Learning",
    "Recovery",
    "Challenge",
    "Analytics",
    "AI",
    "Planner",
    "Library",
    "Management",
    "My Learning",
)
STATE_VERSION = 1
_DEFAULT_DATA_PATH = Path(".ule_data") / "world_state.json"
_STATE_LOCK = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _identifier(prefix: str, *parts: object) -> str:
    source = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def _clean_text(value: object, *, maximum: int = 4000) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:maximum]


def default_world_state() -> dict:
    return {
        "version": STATE_VERSION,
        "rounds": [],
        "recovery_sessions": [],
        "planner": {"goals": [], "schedule": []},
        "library": {"resources": [], "notes": []},
        "management": {
            "subjects": [],
            "settings": {
                "default_question_count": 5,
                "default_difficulty": "Easy",
            },
        },
        "ai_history": [],
        "activity": [],
    }


def normalize_world_state(value: object) -> dict:
    state = copy.deepcopy(value) if isinstance(value, dict) else default_world_state()
    baseline = default_world_state()
    if state.get("version") != STATE_VERSION:
        state["version"] = STATE_VERSION

    for key in ("rounds", "recovery_sessions", "ai_history", "activity"):
        if not isinstance(state.get(key), list):
            state[key] = []

    for section in ("planner", "library", "management"):
        if not isinstance(state.get(section), dict):
            state[section] = copy.deepcopy(baseline[section])

    for key in ("goals", "schedule"):
        if not isinstance(state["planner"].get(key), list):
            state["planner"][key] = []
    for key in ("resources", "notes"):
        if not isinstance(state["library"].get(key), list):
            state["library"][key] = []
    if not isinstance(state["management"].get("subjects"), list):
        state["management"]["subjects"] = []
    if not isinstance(state["management"].get("settings"), dict):
        state["management"]["settings"] = copy.deepcopy(
            baseline["management"]["settings"]
        )

    settings = state["management"]["settings"]
    if settings.get("default_question_count") not in (5, 10, 15, 20):
        settings["default_question_count"] = 5
    if settings.get("default_difficulty") not in (
        "Easy",
        "Normal",
        "Hard",
        "Nightmare",
    ):
        settings["default_difficulty"] = "Easy"

    state["rounds"] = [
        item for item in state["rounds"] if isinstance(item, dict) and item.get("id")
    ][-500:]
    state["recovery_sessions"] = [
        item
        for item in state["recovery_sessions"]
        if isinstance(item, dict) and item.get("id")
    ][-500:]
    state["ai_history"] = [
        item for item in state["ai_history"] if isinstance(item, dict)
    ][-100:]
    state["activity"] = [
        item for item in state["activity"] if isinstance(item, dict)
    ][-500:]
    return state


def data_path() -> Path:
    configured = os.getenv("ULE_DATA_PATH")
    return Path(configured).expanduser() if configured else _DEFAULT_DATA_PATH


def load_world_state(path: Path | None = None) -> dict:
    target = path or data_path()
    with _STATE_LOCK:
        if not target.exists():
            return default_world_state()
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default_world_state()
        return normalize_world_state(payload)


def save_world_state(state: dict, path: Path | None = None) -> None:
    target = path or data_path()
    payload = normalize_world_state(state)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with _STATE_LOCK:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, target)


def export_world_state(state: dict) -> str:
    return json.dumps(normalize_world_state(state), ensure_ascii=False, indent=2)


def import_world_state(text: str) -> dict:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("백업 데이터가 올바른 객체 형식이 아닙니다.")
    return normalize_world_state(payload)


def add_activity(
    state: dict,
    world: str,
    action: str,
    *,
    topic: str = "",
    reference_id: str = "",
) -> None:
    if world not in WORLD_NAMES:
        raise ValueError("지원하지 않는 World입니다.")
    state["activity"].append(
        {
            "world": world,
            "action": _clean_text(action, maximum=200),
            "topic": _clean_text(topic, maximum=80),
            "reference_id": _clean_text(reference_id, maximum=80),
            "created_at": _now(),
        }
    )
    state["activity"] = state["activity"][-500:]


def _wrong_items(lesson: dict, answers: dict) -> list[dict]:
    items = []
    for index, question in enumerate(lesson.get("cbt", [])):
        selected = answers.get(index)
        answer_index = question.get("answer_index")
        if selected == answer_index:
            continue
        item_id = _identifier(
            "wrong",
            lesson.get("topic"),
            lesson.get("difficulty"),
            index,
            question.get("question"),
            answer_index,
        )
        items.append(
            {
                "id": item_id,
                "question_index": index,
                "question": _clean_text(question.get("question")),
                "choices": [
                    _clean_text(choice, maximum=1000)
                    for choice in question.get("choices", [])
                ],
                "answer_index": answer_index,
                "selected_index": selected,
                "explanation": _clean_text(question.get("explanation")),
                "recovered": False,
                "recovered_at": None,
            }
        )
    return items


def record_completed_round(
    state: dict,
    lesson: dict,
    answers: dict,
    *,
    origin: str = "Learning",
    duration_seconds: int = 0,
) -> dict:
    topic = _clean_text(lesson.get("topic"), maximum=80)
    questions = lesson.get("cbt", [])
    fingerprint_parts = [
        topic,
        lesson.get("difficulty"),
        origin,
        *[question.get("question") for question in questions if isinstance(question, dict)],
        *[answers.get(index) for index in range(len(questions))],
    ]
    round_id = _identifier("round", *fingerprint_parts)
    existing = next(
        (item for item in state["rounds"] if item.get("id") == round_id),
        None,
    )
    if existing:
        return existing

    correct_count = sum(
        answers.get(index) == question.get("answer_index")
        for index, question in enumerate(questions)
    )
    question_count = len(questions)
    wrong_items = _wrong_items(lesson, answers)
    record = {
        "id": round_id,
        "origin": origin if origin in ("Learning", "Challenge") else "Learning",
        "challenge_mode": _clean_text(lesson.get("challenge_mode"), maximum=40),
        "topic": topic,
        "difficulty": _clean_text(lesson.get("difficulty"), maximum=40),
        "question_count": question_count,
        "correct_count": correct_count,
        "wrong_count": question_count - correct_count,
        "accuracy": (correct_count / question_count * 100) if question_count else 0.0,
        "duration_seconds": max(0, int(duration_seconds)),
        "wrong_items": wrong_items,
        "created_at": _now(),
    }
    state["rounds"].append(record)

    subjects = state["management"]["subjects"]
    if topic and topic not in subjects:
        subjects.append(topic)
        subjects.sort(key=str.casefold)

    resource = {
        "id": _identifier("resource", round_id),
        "topic": topic,
        "title": f"{topic} 학습자료",
        "tutorial": _clean_text(lesson.get("tutorial")),
        "example": _clean_text(lesson.get("example")),
        "direct_task": _clean_text(lesson.get("direct_task")),
        "practice": _clean_text(lesson.get("practice")),
        "created_at": record["created_at"],
        "source_round_id": round_id,
    }
    if not any(
        item.get("id") == resource["id"] for item in state["library"]["resources"]
    ):
        state["library"]["resources"].append(resource)

    add_activity(
        state,
        record["origin"],
        "학습 라운드 완료",
        topic=topic,
        reference_id=round_id,
    )
    if wrong_items:
        add_activity(
            state,
            "Recovery",
            f"복습 대기 문제 {len(wrong_items)}개 생성",
            topic=topic,
            reference_id=round_id,
        )
    return record


def pending_recovery_items(state: dict, topic: str | None = None) -> list[dict]:
    items = []
    for record in reversed(state["rounds"]):
        if topic and record.get("topic") != topic:
            continue
        for item in record.get("wrong_items", []):
            if isinstance(item, dict) and not item.get("recovered"):
                items.append(
                    {
                        **item,
                        "round_id": record.get("id"),
                        "topic": record.get("topic", ""),
                        "difficulty": record.get("difficulty", ""),
                    }
                )
    return items


def start_recovery_session(
    state: dict, item_ids: Iterable[str] | None = None
) -> dict:
    pending = pending_recovery_items(state)
    selected_ids = set(item_ids or [item["id"] for item in pending])
    selected = [item for item in pending if item["id"] in selected_ids]
    if not selected:
        raise ValueError("복습할 오답이 없습니다.")
    session_id = _identifier(
        "recovery",
        _now(),
        *[item["id"] for item in selected],
        len(state["recovery_sessions"]),
    )
    session = {
        "id": session_id,
        "status": "active",
        "item_ids": [item["id"] for item in selected],
        "answers": {},
        "correct_count": 0,
        "question_count": len(selected),
        "topics": sorted({item["topic"] for item in selected}),
        "created_at": _now(),
        "completed_at": None,
    }
    state["recovery_sessions"].append(session)
    add_activity(
        state,
        "Recovery",
        f"Recovery Session 시작 ({len(selected)}문제)",
        reference_id=session_id,
    )
    return session


def recovery_session_items(state: dict, session: dict) -> list[dict]:
    wanted = set(session.get("item_ids", []))
    return [item for item in pending_recovery_items(state) if item["id"] in wanted]


def submit_recovery_answer(
    state: dict, session_id: str, item_id: str, selected_index: int
) -> bool:
    session = next(
        (item for item in state["recovery_sessions"] if item.get("id") == session_id),
        None,
    )
    if not session or session.get("status") != "active":
        raise ValueError("활성 Recovery Session을 찾을 수 없습니다.")
    if item_id not in session.get("item_ids", []):
        raise ValueError("Recovery Session에 포함되지 않은 문제입니다.")
    item = next(
        (candidate for candidate in pending_recovery_items(state) if candidate["id"] == item_id),
        None,
    )
    if not item:
        raise ValueError("복습 문제를 찾을 수 없습니다.")
    if type(selected_index) is not int or selected_index not in range(len(item["choices"])):
        raise ValueError("올바른 답을 선택해주세요.")
    is_correct = selected_index == item["answer_index"]
    session["answers"][item_id] = {
        "selected_index": selected_index,
        "is_correct": is_correct,
        "answered_at": _now(),
    }
    return is_correct


def complete_recovery_session(state: dict, session_id: str) -> dict:
    session = next(
        (item for item in state["recovery_sessions"] if item.get("id") == session_id),
        None,
    )
    if not session or session.get("status") != "active":
        raise ValueError("활성 Recovery Session을 찾을 수 없습니다.")
    if len(session.get("answers", {})) != session.get("question_count"):
        raise ValueError("모든 복습 문제에 답해주세요.")

    correct_ids = {
        item_id
        for item_id, answer in session["answers"].items()
        if answer.get("is_correct")
    }
    for record in state["rounds"]:
        for item in record.get("wrong_items", []):
            if item.get("id") in correct_ids:
                item["recovered"] = True
                item["recovered_at"] = _now()

    session["status"] = "completed"
    session["correct_count"] = len(correct_ids)
    session["completed_at"] = _now()
    add_activity(
        state,
        "Recovery",
        (
            f"Recovery Session 완료 "
            f"({session['correct_count']}/{session['question_count']})"
        ),
        reference_id=session_id,
    )
    return session


def add_goal(state: dict, title: str, target_date: str = "") -> dict:
    cleaned = _clean_text(title, maximum=200)
    if not cleaned:
        raise ValueError("목표를 입력해주세요.")
    goal = {
        "id": _identifier("goal", cleaned, target_date, _now()),
        "title": cleaned,
        "target_date": _clean_text(target_date, maximum=10),
        "completed": False,
        "created_at": _now(),
    }
    state["planner"]["goals"].append(goal)
    add_activity(state, "Planner", "학습 목표 등록", reference_id=goal["id"])
    return goal


def set_goal_completed(state: dict, goal_id: str, completed: bool) -> dict:
    goal = next(
        (item for item in state["planner"]["goals"] if item.get("id") == goal_id),
        None,
    )
    if not goal:
        raise ValueError("목표를 찾을 수 없습니다.")
    goal["completed"] = bool(completed)
    add_activity(
        state,
        "Planner",
        "학습 목표 완료" if completed else "학습 목표 다시 열기",
        reference_id=goal_id,
    )
    return goal


def add_schedule(
    state: dict, title: str, scheduled_date: str, world: str, topic: str = ""
) -> dict:
    cleaned = _clean_text(title, maximum=200)
    if not cleaned:
        raise ValueError("일정 제목을 입력해주세요.")
    try:
        date.fromisoformat(scheduled_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("올바른 일정 날짜를 선택해주세요.") from exc
    if world not in WORLD_NAMES:
        raise ValueError("올바른 World를 선택해주세요.")
    item = {
        "id": _identifier("schedule", cleaned, scheduled_date, world, _now()),
        "title": cleaned,
        "scheduled_date": scheduled_date,
        "world": world,
        "topic": _clean_text(topic, maximum=80),
        "completed": False,
        "created_at": _now(),
    }
    state["planner"]["schedule"].append(item)
    add_activity(
        state,
        "Planner",
        f"{world} 일정 등록",
        topic=item["topic"],
        reference_id=item["id"],
    )
    return item


def today_schedule(state: dict, today: str | None = None) -> list[dict]:
    target = today or date.today().isoformat()
    return [
        item
        for item in state["planner"]["schedule"]
        if item.get("scheduled_date") == target and not item.get("completed")
    ]


def add_note(state: dict, title: str, content: str, topic: str = "") -> dict:
    clean_title = _clean_text(title, maximum=200)
    clean_content = _clean_text(content, maximum=12000)
    if not clean_title or not clean_content:
        raise ValueError("노트 제목과 내용을 모두 입력해주세요.")
    note = {
        "id": _identifier("note", clean_title, clean_content, _now()),
        "title": clean_title,
        "content": clean_content,
        "topic": _clean_text(topic, maximum=80),
        "created_at": _now(),
    }
    state["library"]["notes"].append(note)
    add_activity(
        state,
        "Library",
        "노트 저장",
        topic=note["topic"],
        reference_id=note["id"],
    )
    return note


def search_library(state: dict, query: str) -> list[dict]:
    normalized = _clean_text(query, maximum=200).casefold()
    if not normalized:
        return []
    results = []
    for resource in state["library"]["resources"]:
        haystack = " ".join(
            str(resource.get(key, ""))
            for key in (
                "title",
                "topic",
                "tutorial",
                "example",
                "direct_task",
                "practice",
            )
        ).casefold()
        if normalized in haystack:
            results.append({"kind": "학습자료", **resource})
    for note in state["library"]["notes"]:
        haystack = " ".join(
            str(note.get(key, "")) for key in ("title", "topic", "content")
        ).casefold()
        if normalized in haystack:
            results.append({"kind": "노트", **note})
    return results


def add_ai_history(
    state: dict, kind: str, prompt: str, response: str, topic: str = ""
) -> dict:
    if kind not in ("질문", "추천", "요약"):
        raise ValueError("지원하지 않는 AI 기능입니다.")
    item = {
        "kind": kind,
        "prompt": _clean_text(prompt),
        "response": _clean_text(response, maximum=12000),
        "topic": _clean_text(topic, maximum=80),
        "created_at": _now(),
    }
    state["ai_history"].append(item)
    state["ai_history"] = state["ai_history"][-100:]
    add_activity(state, "AI", f"AI {kind} 완료", topic=item["topic"])
    return item


def learning_stats(state: dict) -> dict:
    rounds = state["rounds"]
    total_questions = sum(max(0, int(item.get("question_count", 0))) for item in rounds)
    correct_count = sum(max(0, int(item.get("correct_count", 0))) for item in rounds)
    study_seconds = sum(max(0, int(item.get("duration_seconds", 0))) for item in rounds)
    completed_recovery = [
        item
        for item in state["recovery_sessions"]
        if item.get("status") == "completed"
    ]
    points = correct_count * 10 + len(rounds) * 20 + len(completed_recovery) * 15
    level = points // 100 + 1
    achievements = []
    if rounds:
        achievements.append("첫 학습 완료")
    if len(rounds) >= 5:
        achievements.append("꾸준한 학습자")
    if any(float(item.get("accuracy", 0)) >= 100 for item in rounds):
        achievements.append("완벽한 라운드")
    if completed_recovery:
        achievements.append("회복 학습 시작")
    if sum(item.get("correct_count", 0) for item in completed_recovery) >= 10:
        achievements.append("오답 정복자")
    return {
        "round_count": len(rounds),
        "question_count": total_questions,
        "correct_count": correct_count,
        "accuracy": (correct_count / total_questions * 100) if total_questions else 0.0,
        "study_seconds": study_seconds,
        "level": level,
        "points": points,
        "achievements": achievements,
        "topic_count": len({item.get("topic") for item in rounds if item.get("topic")}),
        "recovery_count": len(completed_recovery),
    }


def build_report(state: dict) -> str:
    stats = learning_stats(state)
    lines = [
        "# Universal Learning Engine 학습 리포트",
        "",
        f"- 완료 라운드: {stats['round_count']}",
        f"- 학습 주제: {stats['topic_count']}",
        f"- 분석 문항: {stats['question_count']}",
        f"- 전체 정확도: {stats['accuracy']:.1f}%",
        f"- Recovery Session: {stats['recovery_count']}",
        f"- 공부시간: {stats['study_seconds'] // 60}분",
        f"- 레벨: {stats['level']}",
        "",
        "## 최근 학습",
    ]
    for item in reversed(state["rounds"][-10:]):
        lines.append(
            f"- {item.get('topic', '-')} / {item.get('difficulty', '-')} / "
            f"{float(item.get('accuracy', 0)):.1f}%"
        )
    if not state["rounds"]:
        lines.append("- 기록 없음")
    return "\n".join(lines)
