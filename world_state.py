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
CHALLENGE_MODES = ("Exam", "Hard", "Nightmare", "모의고사")
WORLD_LABELS = {
    "Learning": "학습",
    "Recovery": "회복 학습",
    "Challenge": "도전 학습",
    "Analytics": "학습 분석",
    "AI": "인공지능",
    "Planner": "학습 계획",
    "Library": "학습 자료실",
    "Management": "관리",
    "My Learning": "나의 학습",
}
DIFFICULTY_LABELS = {
    "Easy": "기초",
    "Normal": "보통",
    "Hard": "심화",
    "Nightmare": "최고 난도",
}
CHALLENGE_MODE_LABELS = {
    "Exam": "시험",
    "Hard": "심화",
    "Nightmare": "최고 난도",
    "모의고사": "모의고사",
}
RESOURCE_KIND_LABELS = {
    "Learning Resource": "학습 자료",
    "Recovery Record": "회복 학습 기록",
    "Challenge Result": "도전 학습 결과",
    "Planner Goal": "학습 목표",
    "Planner Schedule": "학습 일정",
    "학습자료": "학습 자료",
}
RECORD_CATEGORY_LABELS = {
    "learning": "학습 기록",
    "recovery": "회복 학습 기록",
    "challenge": "도전 학습 기록",
    "ai": "인공지능 기록",
    "planner": "학습 계획 기록",
    "library": "학습 자료실 기록",
}
STATE_VERSION = 2
_DEFAULT_DATA_PATH = Path(".ule_data") / "world_state.json"
_STATE_LOCK = threading.RLock()


def world_label(value: object) -> str:
    return WORLD_LABELS.get(str(value), str(value))


def difficulty_label(value: object) -> str:
    return DIFFICULTY_LABELS.get(str(value), str(value))


def challenge_mode_label(value: object) -> str:
    return CHALLENGE_MODE_LABELS.get(str(value), str(value))


def resource_kind_label(value: object) -> str:
    text = str(value)
    if text.startswith("AI "):
        return "인공지능 " + text.removeprefix("AI ")
    return RESOURCE_KIND_LABELS.get(text, text)


def localized_record_text(value: object) -> str:
    """Localize system-generated labels while preserving user-authored text."""
    text = str(value)
    replacements = (
        ("Recovery Recommendation", "회복 학습 추천"),
        ("Recovery Session", "회복 학습"),
        ("Challenge Session", "도전 학습"),
        ("Challenge Result", "도전 학습 결과"),
        ("Learning Resource", "학습 자료"),
        ("Planner Schedule", "학습 일정"),
        ("Planner Goal", "학습 목표"),
        ("AI 추천 학습", "인공지능 추천 학습"),
        ("AI 추천", "인공지능 추천"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    return text


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
        "recovery_recommendations": [],
        "challenge": {"sessions": [], "results": []},
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

    for key in (
        "rounds",
        "recovery_sessions",
        "recovery_recommendations",
        "ai_history",
        "activity",
    ):
        if not isinstance(state.get(key), list):
            state[key] = []

    for section in ("challenge", "planner", "library", "management"):
        if not isinstance(state.get(section), dict):
            state[section] = copy.deepcopy(baseline[section])

    for key in ("sessions", "results"):
        if not isinstance(state["challenge"].get(key), list):
            state["challenge"][key] = []
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
    state["recovery_recommendations"] = [
        item
        for item in state["recovery_recommendations"]
        if isinstance(item, dict) and item.get("id")
    ][-500:]
    state["challenge"]["sessions"] = [
        item
        for item in state["challenge"]["sessions"]
        if isinstance(item, dict) and item.get("id")
    ][-500:]
    state["challenge"]["results"] = [
        item
        for item in state["challenge"]["results"]
        if isinstance(item, dict) and item.get("id")
    ][-500:]
    state["ai_history"] = [
        item for item in state["ai_history"] if isinstance(item, dict)
    ][-100:]
    for index, item in enumerate(state["ai_history"]):
        item.setdefault(
            "id",
            _identifier(
                "ai",
                item.get("kind"),
                item.get("prompt"),
                item.get("response"),
                item.get("created_at"),
                index,
            ),
        )
        item.setdefault(
            "planner_link",
            {
                "status": (
                    "available"
                    if item.get("kind") == "추천"
                    else "not_applicable"
                ),
                "goal_id": "",
                "schedule_id": "",
                "linked_at": None,
            },
        )
    for item in state["planner"]["goals"]:
        if isinstance(item, dict):
            item.setdefault("topic", "")
            item.setdefault("source_ai_id", "")
    for item in state["planner"]["schedule"]:
        if isinstance(item, dict):
            item.setdefault("source_ai_id", "")
    for item in state["library"]["resources"]:
        if not isinstance(item, dict):
            continue
        item.setdefault("source_world", "Learning")
        item.setdefault(
            "source_id",
            item.get("source_round_id") or item.get("id", ""),
        )
        item.setdefault("kind", "Learning Resource")
        item.setdefault(
            "content",
            "\n\n".join(
                str(item.get(key, "")).strip()
                for key in ("tutorial", "example", "direct_task", "practice")
                if str(item.get(key, "")).strip()
            ),
        )
        item.setdefault("details", {})
    state["activity"] = [
        item for item in state["activity"] if isinstance(item, dict)
    ][-500:]
    return state


def _ensure_subject(state: dict, topic: str) -> None:
    cleaned = _clean_text(topic, maximum=80)
    if not cleaned:
        return
    subjects = state["management"]["subjects"]
    if cleaned not in subjects:
        subjects.append(cleaned)
        subjects.sort(key=str.casefold)


def _store_library_resource(
    state: dict,
    *,
    source_world: str,
    source_id: str,
    kind: str,
    title: str,
    content: str,
    topic: str = "",
    details: dict | None = None,
) -> dict:
    resource_id = _identifier("resource", source_world, source_id, kind)
    existing = next(
        (
            item
            for item in state["library"]["resources"]
            if item.get("id") == resource_id
        ),
        None,
    )
    if existing:
        return existing
    resource = {
        "id": resource_id,
        "source_world": source_world,
        "source_id": _clean_text(source_id, maximum=80),
        "kind": _clean_text(kind, maximum=80),
        "title": _clean_text(title, maximum=200),
        "content": _clean_text(content, maximum=12000),
        "topic": _clean_text(topic, maximum=80),
        "details": copy.deepcopy(details) if isinstance(details, dict) else {},
        "created_at": _now(),
    }
    state["library"]["resources"].append(resource)
    state["library"]["resources"] = state["library"]["resources"][-1000:]
    _ensure_subject(state, resource["topic"])
    return resource


def _seconds_between(started_at: object, completed_at: object) -> int:
    if not isinstance(started_at, str) or not isinstance(completed_at, str):
        return 0
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(completed_at)
    except ValueError:
        return 0
    return max(0, round((end - start).total_seconds()))


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


def _record_date(item: dict) -> str:
    value = item.get("completed_at") or item.get("created_at") or ""
    return str(value)[:10] if value else "날짜 없음"


def deletion_catalog(state: dict) -> list[dict]:
    """Return user-selectable records without exposing storage identifiers."""
    normalized = normalize_world_state(state)
    entries: list[dict] = []

    for item in normalized["rounds"]:
        if item.get("origin") != "Learning":
            continue
        entries.append(
            {
                "token": f"round:{item['id']}",
                "category": "learning",
                "label": (
                    f"학습 · {item.get('topic') or '주제 없음'} · "
                    f"{difficulty_label(item.get('difficulty'))} · "
                    f"{float(item.get('accuracy', 0)):.1f}% · {_record_date(item)}"
                ),
            }
        )

    for item in normalized["recovery_sessions"]:
        status = "완료" if item.get("status") == "completed" else "진행 중"
        entries.append(
            {
                "token": f"recovery:{item['id']}",
                "category": "recovery",
                "label": (
                    f"회복 학습 · {', '.join(item.get('topics', [])) or '복습'} · "
                    f"{status} · {_record_date(item)}"
                ),
            }
        )

    result_by_session = {
        item.get("session_id"): item
        for item in normalized["challenge"]["results"]
        if item.get("session_id")
    }
    cataloged_results: set[str] = set()
    for session in normalized["challenge"]["sessions"]:
        result = result_by_session.get(session.get("id"), {})
        if result.get("id"):
            cataloged_results.add(result["id"])
        entries.append(
            {
                "token": f"challenge:{session['id']}",
                "category": "challenge",
                "label": (
                    f"도전 학습 · {challenge_mode_label(session.get('mode'))} · "
                    f"{session.get('topic') or '주제 없음'} · "
                    f"{float(result.get('accuracy', 0)):.1f}% · "
                    f"{_record_date(result or session)}"
                ),
            }
        )
    for result in normalized["challenge"]["results"]:
        if result.get("id") in cataloged_results:
            continue
        entries.append(
            {
                "token": f"challenge_result:{result['id']}",
                "category": "challenge",
                "label": (
                    f"도전 학습 결과 · {challenge_mode_label(result.get('mode'))} · "
                    f"{result.get('topic') or '주제 없음'} · "
                    f"{float(result.get('accuracy', 0)):.1f}% · "
                    f"{_record_date(result)}"
                ),
            }
        )

    for item in normalized["ai_history"]:
        entries.append(
            {
                "token": f"ai:{item['id']}",
                "category": "ai",
                "label": (
                    f"인공지능 {item.get('kind') or '기록'} · "
                    f"{item.get('topic') or '주제 없음'} · {_record_date(item)}"
                ),
            }
        )

    for item in normalized["planner"]["goals"]:
        entries.append(
            {
                "token": f"goal:{item['id']}",
                "category": "planner",
                "label": (
                    f"학습 목표 · "
                    f"{localized_record_text(item.get('title') or '제목 없음')}"
                ),
            }
        )
    for item in normalized["planner"]["schedule"]:
        entries.append(
            {
                "token": f"schedule:{item['id']}",
                "category": "planner",
                "label": (
                    f"학습 일정 · "
                    f"{localized_record_text(item.get('title') or '제목 없음')} · "
                    f"{item.get('scheduled_date') or '날짜 없음'}"
                ),
            }
        )

    for item in normalized["library"]["resources"]:
        entries.append(
            {
                "token": f"resource:{item['id']}",
                "category": "library",
                "label": (
                    f"{resource_kind_label(item.get('kind'))} · "
                    f"{localized_record_text(item.get('title') or '제목 없음')}"
                ),
            }
        )
    for item in normalized["library"]["notes"]:
        entries.append(
            {
                "token": f"note:{item['id']}",
                "category": "library",
                "label": f"노트 · {item.get('title') or '제목 없음'}",
            }
        )
    return entries


def delete_selected_records(state: dict, tokens: Iterable[str]) -> int:
    """Delete selected user records and their dependent generated evidence."""
    valid_catalog = {item["token"] for item in deletion_catalog(state)}
    selected = {
        token for token in tokens if isinstance(token, str) and token in valid_catalog
    }
    if not selected:
        return 0

    selected_by_kind: dict[str, set[str]] = {}
    for token in selected:
        kind, identifier = token.split(":", 1)
        selected_by_kind.setdefault(kind, set()).add(identifier)

    round_ids = set(selected_by_kind.get("round", set()))
    recovery_ids = set(selected_by_kind.get("recovery", set()))
    challenge_session_ids = set(selected_by_kind.get("challenge", set()))
    challenge_result_ids = set(selected_by_kind.get("challenge_result", set()))
    ai_ids = set(selected_by_kind.get("ai", set()))
    goal_ids = set(selected_by_kind.get("goal", set()))
    schedule_ids = set(selected_by_kind.get("schedule", set()))
    resource_ids = set(selected_by_kind.get("resource", set()))
    note_ids = set(selected_by_kind.get("note", set()))

    for result in state["challenge"]["results"]:
        if (
            result.get("id") in challenge_result_ids
            or result.get("session_id") in challenge_session_ids
        ):
            challenge_result_ids.add(result.get("id", ""))
            round_ids.add(result.get("round_id", ""))
            challenge_session_ids.add(result.get("session_id", ""))
    for session in state["challenge"]["sessions"]:
        if (
            session.get("id") in challenge_session_ids
            or session.get("round_id") in round_ids
        ):
            challenge_session_ids.add(session.get("id", ""))
            round_ids.add(session.get("round_id", ""))
            challenge_result_ids.add(session.get("result_id", ""))

    round_ids.discard("")
    challenge_session_ids.discard("")
    challenge_result_ids.discard("")
    wrong_item_ids = {
        wrong.get("id")
        for record in state["rounds"]
        if record.get("id") in round_ids
        for wrong in record.get("wrong_items", [])
        if isinstance(wrong, dict) and wrong.get("id")
    }
    for session in state["recovery_sessions"]:
        if wrong_item_ids.intersection(session.get("item_ids", [])):
            recovery_ids.add(session.get("id", ""))
    recovery_ids.discard("")

    recommendation_ids = {
        item.get("id")
        for item in state["recovery_recommendations"]
        if item.get("recovery_session_id") in recovery_ids
    }
    recommendation_ids.discard(None)
    for item in state["planner"]["goals"]:
        if item.get("source_ai_id") in ai_ids:
            goal_ids.add(item.get("id", ""))
    for item in state["planner"]["schedule"]:
        if item.get("source_ai_id") in ai_ids:
            schedule_ids.add(item.get("id", ""))
    goal_ids.discard("")
    schedule_ids.discard("")

    removed_reference_ids = (
        round_ids
        | recovery_ids
        | recommendation_ids
        | challenge_session_ids
        | challenge_result_ids
        | ai_ids
        | goal_ids
        | schedule_ids
        | resource_ids
        | note_ids
    )

    state["rounds"] = [
        item for item in state["rounds"] if item.get("id") not in round_ids
    ]
    state["recovery_sessions"] = [
        item
        for item in state["recovery_sessions"]
        if item.get("id") not in recovery_ids
    ]
    state["recovery_recommendations"] = [
        item
        for item in state["recovery_recommendations"]
        if item.get("id") not in recommendation_ids
    ]
    state["challenge"]["sessions"] = [
        item
        for item in state["challenge"]["sessions"]
        if item.get("id") not in challenge_session_ids
    ]
    state["challenge"]["results"] = [
        item
        for item in state["challenge"]["results"]
        if item.get("id") not in challenge_result_ids
    ]
    state["ai_history"] = [
        item for item in state["ai_history"] if item.get("id") not in ai_ids
    ]
    state["planner"]["goals"] = [
        item for item in state["planner"]["goals"] if item.get("id") not in goal_ids
    ]
    state["planner"]["schedule"] = [
        item
        for item in state["planner"]["schedule"]
        if item.get("id") not in schedule_ids
    ]
    state["library"]["resources"] = [
        item
        for item in state["library"]["resources"]
        if item.get("id") not in resource_ids
        and item.get("source_id") not in removed_reference_ids
    ]
    state["library"]["notes"] = [
        item for item in state["library"]["notes"] if item.get("id") not in note_ids
    ]
    state["activity"] = [
        item
        for item in state["activity"]
        if item.get("reference_id") not in removed_reference_ids
    ]

    for recommendation in state["recovery_recommendations"]:
        if recommendation.get("challenge_session_id") in challenge_session_ids:
            recommendation["challenge_session_id"] = ""
            recommendation["status"] = "pending"
            recommendation["accepted_at"] = None
    for item in state["ai_history"]:
        link = item.get("planner_link")
        if not isinstance(link, dict):
            continue
        if link.get("goal_id") in goal_ids or link.get("schedule_id") in schedule_ids:
            link.update(
                {
                    "status": "available" if item.get("kind") == "추천" else "not_applicable",
                    "goal_id": "",
                    "schedule_id": "",
                    "linked_at": None,
                }
            )
    return len(selected)


def clear_record_category(state: dict, category: str) -> int:
    if category not in RECORD_CATEGORY_LABELS:
        raise ValueError("지원하지 않는 기록 종류입니다.")
    tokens = [
        item["token"]
        for item in deletion_catalog(state)
        if item["category"] == category
    ]
    return delete_selected_records(state, tokens)


def clear_all_records(state: dict) -> int:
    """Clear learning records while preserving subjects and user defaults."""
    count = len(deletion_catalog(state))
    management = copy.deepcopy(normalize_world_state(state)["management"])
    state.clear()
    state.update(default_world_state())
    state["management"] = management
    return count


def reset_user_data(state: dict) -> int:
    """Restore all durable user data and settings to application defaults."""
    count = len(deletion_catalog(state))
    state.clear()
    state.update(default_world_state())
    return count


def add_activity(
    state: dict,
    world: str,
    action: str,
    *,
    topic: str = "",
    reference_id: str = "",
) -> None:
    if world not in WORLD_NAMES:
        raise ValueError("지원하지 않는 학습 영역입니다.")
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


def start_challenge_session(
    state: dict,
    mode: str,
    topic: str,
    difficulty: str,
    question_count: int,
    *,
    source_recovery_recommendation_id: str = "",
) -> dict:
    if mode not in CHALLENGE_MODES:
        raise ValueError("지원하지 않는 도전 유형입니다.")
    cleaned_topic = _clean_text(topic, maximum=80)
    if not cleaned_topic:
        raise ValueError("도전 학습 주제가 필요합니다.")
    if difficulty not in ("Easy", "Normal", "Hard", "Nightmare"):
        raise ValueError("지원하지 않는 도전 난이도입니다.")
    if question_count not in (5, 10, 15, 20):
        raise ValueError("지원하지 않는 도전 문제 수입니다.")
    session_id = _identifier(
        "challenge",
        mode,
        cleaned_topic,
        difficulty,
        question_count,
        _now(),
        len(state["challenge"]["sessions"]),
    )
    session = {
        "id": session_id,
        "mode": mode,
        "topic": cleaned_topic,
        "difficulty": difficulty,
        "question_count": question_count,
        "status": "active",
        "source_recovery_recommendation_id": _clean_text(
            source_recovery_recommendation_id,
            maximum=80,
        ),
        "round_id": "",
        "result_id": "",
        "started_at": _now(),
        "completed_at": None,
    }
    state["challenge"]["sessions"].append(session)
    if session["source_recovery_recommendation_id"]:
        recommendation = next(
            (
                item
                for item in state["recovery_recommendations"]
                if item.get("id")
                == session["source_recovery_recommendation_id"]
            ),
            None,
        )
        if recommendation:
            recommendation["status"] = "started"
            recommendation["challenge_session_id"] = session_id
    _ensure_subject(state, cleaned_topic)
    add_activity(
        state,
        "Challenge",
        f"{challenge_mode_label(mode)} 도전 시작",
        topic=cleaned_topic,
        reference_id=session_id,
    )
    return session


def complete_challenge_session(
    state: dict,
    session_id: str,
    round_record: dict,
) -> dict:
    session = next(
        (
            item
            for item in state["challenge"]["sessions"]
            if item.get("id") == session_id
        ),
        None,
    )
    if not session:
        raise ValueError("도전 학습 기록을 찾을 수 없습니다.")
    if session.get("status") == "completed":
        existing_id = session.get("result_id")
        return next(
            (
                item
                for item in state["challenge"]["results"]
                if item.get("id") == existing_id
            ),
            {},
        )
    if session.get("status") != "active":
        raise ValueError("진행 중인 도전 학습이 아닙니다.")

    completed_at = _now()
    result_id = _identifier("challenge_result", session_id, round_record.get("id"))
    result = {
        "id": result_id,
        "session_id": session_id,
        "round_id": round_record.get("id", ""),
        "mode": session["mode"],
        "topic": session["topic"],
        "difficulty": session["difficulty"],
        "question_count": round_record.get("question_count", 0),
        "correct_count": round_record.get("correct_count", 0),
        "wrong_count": round_record.get("wrong_count", 0),
        "accuracy": float(round_record.get("accuracy", 0)),
        "duration_seconds": max(0, int(round_record.get("duration_seconds", 0))),
        "completed_at": completed_at,
        "source_recovery_recommendation_id": session.get(
            "source_recovery_recommendation_id",
            "",
        ),
    }
    state["challenge"]["results"].append(result)
    session["status"] = "completed"
    session["round_id"] = result["round_id"]
    session["result_id"] = result_id
    session["completed_at"] = completed_at

    source_id = session.get("source_recovery_recommendation_id")
    if source_id:
        recommendation = next(
            (
                item
                for item in state["recovery_recommendations"]
                if item.get("id") == source_id
            ),
            None,
        )
        if recommendation:
            recommendation["challenge_session_id"] = session_id
            recommendation["status"] = "completed"

    _store_library_resource(
        state,
        source_world="Challenge",
        source_id=result_id,
        kind="Challenge Result",
        title=f"{session['topic']} {challenge_mode_label(session['mode'])} 결과",
        topic=session["topic"],
        content=(
            f"{challenge_mode_label(session['mode'])} · "
            f"{difficulty_label(result['difficulty'])} · "
            f"{result['correct_count']}/{result['question_count']} · "
            f"{result['accuracy']:.1f}%"
        ),
        details=result,
    )
    add_activity(
        state,
        "Challenge",
        f"{challenge_mode_label(session['mode'])} 도전 완료",
        topic=session["topic"],
        reference_id=result_id,
    )
    return result


def challenge_history(state: dict, mode: str | None = None) -> list[dict]:
    results = state["challenge"]["results"]
    if mode is None:
        return list(results)
    return [item for item in results if item.get("mode") == mode]


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
    safe_origin = origin if origin in ("Learning", "Challenge") else "Learning"
    challenge_session_id = _clean_text(
        lesson.get("challenge_session_id"),
        maximum=80,
    )
    if safe_origin == "Challenge" and not challenge_session_id:
        session = start_challenge_session(
            state,
            lesson.get("challenge_mode") or "Exam",
            topic,
            lesson.get("difficulty") or "Normal",
            lesson.get("requested_question_count") or len(questions),
            source_recovery_recommendation_id=lesson.get(
                "source_recovery_recommendation_id",
                "",
            ),
        )
        challenge_session_id = session["id"]
        lesson["challenge_session_id"] = challenge_session_id
    fingerprint_parts = [
        topic,
        lesson.get("difficulty"),
        safe_origin,
        challenge_session_id,
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
        "origin": safe_origin,
        "challenge_mode": _clean_text(lesson.get("challenge_mode"), maximum=40),
        "challenge_session_id": challenge_session_id,
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
    _ensure_subject(state, topic)
    lesson_details = {
        "tutorial": _clean_text(lesson.get("tutorial")),
        "example": _clean_text(lesson.get("example")),
        "direct_task": _clean_text(lesson.get("direct_task")),
        "practice": _clean_text(lesson.get("practice")),
        "difficulty": record["difficulty"],
        "round_id": round_id,
    }
    _store_library_resource(
        state,
        source_world=safe_origin,
        source_id=round_id,
        kind="Learning Resource",
        title=f"{topic} 학습자료",
        topic=topic,
        content="\n\n".join(
            value
            for value in (
                lesson_details["tutorial"],
                lesson_details["example"],
                lesson_details["direct_task"],
                lesson_details["practice"],
            )
            if value
        ),
        details=lesson_details,
    )

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
    if safe_origin == "Challenge" and challenge_session_id:
        complete_challenge_session(state, challenge_session_id, record)
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
        f"회복 학습 시작 ({len(selected)}문제)",
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
        raise ValueError("진행 중인 회복 학습을 찾을 수 없습니다.")
    if item_id not in session.get("item_ids", []):
        raise ValueError("현재 회복 학습에 포함되지 않은 문제입니다.")
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
        raise ValueError("진행 중인 회복 학습을 찾을 수 없습니다.")
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

    completed_at = _now()
    session["status"] = "completed"
    session["correct_count"] = len(correct_ids)
    session["completed_at"] = completed_at
    session["duration_seconds"] = _seconds_between(
        session.get("created_at"),
        completed_at,
    )
    question_count = max(0, int(session.get("question_count", 0)))
    accuracy = (
        session["correct_count"] / question_count * 100
        if question_count
        else 0.0
    )
    topic = ", ".join(session.get("topics", []))
    if accuracy >= 90:
        recommended_mode = "Nightmare"
        reason = "회복 학습 정확도가 90% 이상이므로 최고 난도 적용 학습을 권장합니다."
    elif accuracy >= 70:
        recommended_mode = "Hard"
        reason = "회복 학습 정확도가 70% 이상이므로 심화 적용 학습을 권장합니다."
    else:
        recommended_mode = "Exam"
        reason = "회복 학습 결과를 점검할 수 있도록 시험 학습을 권장합니다."
    recommendation_id = _identifier(
        "recovery_recommendation",
        session_id,
        recommended_mode,
    )
    recommendation = {
        "id": recommendation_id,
        "recovery_session_id": session_id,
        "target_world": "Challenge",
        "mode": recommended_mode,
        "topic": topic,
        "reason": reason,
        "status": "pending",
        "challenge_session_id": "",
        "created_at": completed_at,
        "accepted_at": None,
    }
    state["recovery_recommendations"].append(recommendation)
    session["record"] = {
        "correct_count": session["correct_count"],
        "question_count": question_count,
        "accuracy": accuracy,
        "duration_seconds": session["duration_seconds"],
        "recommendation_id": recommendation_id,
    }
    _store_library_resource(
        state,
        source_world="Recovery",
        source_id=session_id,
        kind="Recovery Record",
        title=f"{topic or '복습'} 회복 학습 기록",
        topic=topic,
        content=(
            f"{session['correct_count']}/{question_count} · {accuracy:.1f}% · "
            f"추천 도전 유형: {challenge_mode_label(recommended_mode)}\n{reason}"
        ),
        details=session["record"],
    )
    add_activity(
        state,
        "Recovery",
        (
            f"회복 학습 완료 "
            f"({session['correct_count']}/{session['question_count']})"
        ),
        reference_id=session_id,
    )
    return session


def recovery_history(state: dict) -> list[dict]:
    return [
        item
        for item in state["recovery_sessions"]
        if item.get("status") == "completed"
    ]


def pending_recovery_recommendations(state: dict) -> list[dict]:
    return [
        item
        for item in state["recovery_recommendations"]
        if item.get("status") == "pending"
    ]


def accept_recovery_recommendation(state: dict, recommendation_id: str) -> dict:
    recommendation = next(
        (
            item
            for item in state["recovery_recommendations"]
            if item.get("id") == recommendation_id
        ),
        None,
    )
    if not recommendation:
        raise ValueError("회복 학습 추천을 찾을 수 없습니다.")
    if recommendation.get("status") == "pending":
        recommendation["status"] = "accepted"
        recommendation["accepted_at"] = _now()
        add_activity(
            state,
            "Recovery",
            "회복 학습 추천 수락",
            topic=recommendation.get("topic", ""),
            reference_id=recommendation_id,
        )
    return recommendation


def add_goal(
    state: dict,
    title: str,
    target_date: str = "",
    *,
    topic: str = "",
    source_ai_id: str = "",
) -> dict:
    cleaned = _clean_text(title, maximum=200)
    if not cleaned:
        raise ValueError("목표를 입력해주세요.")
    goal = {
        "id": _identifier("goal", cleaned, target_date, _now()),
        "title": cleaned,
        "target_date": _clean_text(target_date, maximum=10),
        "topic": _clean_text(topic, maximum=80),
        "source_ai_id": _clean_text(source_ai_id, maximum=80),
        "completed": False,
        "created_at": _now(),
    }
    state["planner"]["goals"].append(goal)
    _store_library_resource(
        state,
        source_world="Planner",
        source_id=goal["id"],
        kind="Planner Goal",
        title=goal["title"],
        topic=goal["topic"],
        content=(
            f"목표일: {goal['target_date'] or '기한 없음'}"
            + (
                f"\n인공지능 추천 연결: {goal['source_ai_id']}"
                if goal["source_ai_id"]
                else ""
            )
        ),
        details=goal,
    )
    add_activity(
        state,
        "Planner",
        "학습 목표 등록",
        topic=goal["topic"],
        reference_id=goal["id"],
    )
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
    state: dict,
    title: str,
    scheduled_date: str,
    world: str,
    topic: str = "",
    *,
    source_ai_id: str = "",
) -> dict:
    cleaned = _clean_text(title, maximum=200)
    if not cleaned:
        raise ValueError("일정 제목을 입력해주세요.")
    try:
        date.fromisoformat(scheduled_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("올바른 일정 날짜를 선택해주세요.") from exc
    if world not in WORLD_NAMES:
        raise ValueError("올바른 학습 영역을 선택해주세요.")
    item = {
        "id": _identifier("schedule", cleaned, scheduled_date, world, _now()),
        "title": cleaned,
        "scheduled_date": scheduled_date,
        "world": world,
        "topic": _clean_text(topic, maximum=80),
        "source_ai_id": _clean_text(source_ai_id, maximum=80),
        "completed": False,
        "created_at": _now(),
    }
    state["planner"]["schedule"].append(item)
    _store_library_resource(
        state,
        source_world="Planner",
        source_id=item["id"],
        kind="Planner Schedule",
        title=item["title"],
        topic=item["topic"],
        content=f"{item['scheduled_date']} · {world_label(item['world'])}",
        details=item,
    )
    add_activity(
        state,
        "Planner",
        f"{world_label(world)} 일정 등록",
        topic=item["topic"],
        reference_id=item["id"],
    )
    return item


def set_schedule_completed(state: dict, schedule_id: str, completed: bool) -> dict:
    item = next(
        (
            candidate
            for candidate in state["planner"]["schedule"]
            if candidate.get("id") == schedule_id
        ),
        None,
    )
    if not item:
        raise ValueError("일정을 찾을 수 없습니다.")
    item["completed"] = bool(completed)
    item["completed_at"] = _now() if completed else None
    add_activity(
        state,
        "Planner",
        "학습 일정 완료" if completed else "학습 일정 다시 열기",
        topic=item.get("topic", ""),
        reference_id=schedule_id,
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
    _ensure_subject(state, note["topic"])
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
                "content",
                "kind",
                "source_world",
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
    if kind not in ("질문", "해설", "추천", "요약"):
        raise ValueError("지원하지 않는 인공지능 기능입니다.")
    created_at = _now()
    cleaned_topic = _clean_text(topic, maximum=80)
    if not cleaned_topic and state["rounds"]:
        cleaned_topic = _clean_text(state["rounds"][-1].get("topic"), maximum=80)
    item = {
        "id": _identifier(
            "ai",
            kind,
            prompt,
            response,
            created_at,
            len(state["ai_history"]),
        ),
        "kind": kind,
        "prompt": _clean_text(prompt),
        "response": _clean_text(response, maximum=12000),
        "topic": cleaned_topic,
        "planner_link": {
            "status": "available" if kind == "추천" else "not_applicable",
            "goal_id": "",
            "schedule_id": "",
            "linked_at": None,
        },
        "created_at": created_at,
    }
    state["ai_history"].append(item)
    state["ai_history"] = state["ai_history"][-100:]
    _store_library_resource(
        state,
        source_world="AI",
        source_id=item["id"],
        kind=f"인공지능 {kind}",
        title=f"{item['topic'] or '학습'} 인공지능 {kind}",
        topic=item["topic"],
        content=item["response"],
        details={"prompt": item["prompt"], "kind": kind},
    )
    add_activity(
        state,
        "AI",
        f"인공지능 {kind} 완료",
        topic=item["topic"],
        reference_id=item["id"],
    )
    return item


def connect_ai_recommendation_to_planner(
    state: dict,
    ai_id: str,
    scheduled_date: str | None = None,
) -> dict:
    item = next(
        (
            candidate
            for candidate in state["ai_history"]
            if candidate.get("id") == ai_id
        ),
        None,
    )
    if not item or item.get("kind") != "추천":
        raise ValueError("학습 계획에 연결할 인공지능 추천을 찾을 수 없습니다.")
    link = item.setdefault(
        "planner_link",
        {
            "status": "available",
            "goal_id": "",
            "schedule_id": "",
            "linked_at": None,
        },
    )
    if link.get("status") == "linked":
        return link

    target_date = scheduled_date or date.today().isoformat()
    try:
        date.fromisoformat(target_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("올바른 학습 계획 날짜가 필요합니다.") from exc
    topic = _clean_text(item.get("topic"), maximum=80) or "다음 학습"
    goal = add_goal(
        state,
        f"{topic} 학습 목표",
        target_date,
        topic=topic,
        source_ai_id=ai_id,
    )
    schedule = add_schedule(
        state,
        f"{topic} 인공지능 추천 학습",
        target_date,
        "Learning",
        topic,
        source_ai_id=ai_id,
    )
    link.update(
        {
            "status": "linked",
            "goal_id": goal["id"],
            "schedule_id": schedule["id"],
            "linked_at": _now(),
        }
    )
    add_activity(
        state,
        "AI",
        "인공지능 추천을 학습 계획에 연결",
        topic=topic,
        reference_id=ai_id,
    )
    return link


def _challenge_evidence(state: dict) -> list[dict]:
    results = list(state["challenge"]["results"])
    result_round_ids = {item.get("round_id") for item in results}
    for record in state["rounds"]:
        if (
            record.get("origin") == "Challenge"
            and record.get("id") not in result_round_ids
        ):
            results.append(
                {
                    "id": f"compatible_{record.get('id', '')}",
                    "session_id": record.get("challenge_session_id", ""),
                    "round_id": record.get("id", ""),
                    "mode": record.get("challenge_mode") or "Exam",
                    "topic": record.get("topic", ""),
                    "difficulty": record.get("difficulty", ""),
                    "question_count": record.get("question_count", 0),
                    "correct_count": record.get("correct_count", 0),
                    "wrong_count": record.get("wrong_count", 0),
                    "accuracy": float(record.get("accuracy", 0)),
                    "duration_seconds": record.get("duration_seconds", 0),
                    "completed_at": record.get("created_at"),
                }
            )
    return results


def build_world_analytics(state: dict) -> dict:
    rounds = state["rounds"]
    learning_rounds = [item for item in rounds if item.get("origin") == "Learning"]
    challenge_results = _challenge_evidence(state)
    recovery_records = recovery_history(state)
    total_questions = sum(
        max(0, int(item.get("question_count", 0)))
        for item in rounds
    )
    correct_count = sum(
        max(0, int(item.get("correct_count", 0)))
        for item in rounds
    )
    challenge_modes = {}
    for mode in CHALLENGE_MODES:
        evidence = [item for item in challenge_results if item.get("mode") == mode]
        questions = sum(max(0, int(item.get("question_count", 0))) for item in evidence)
        correct = sum(max(0, int(item.get("correct_count", 0))) for item in evidence)
        challenge_modes[mode] = {
            "session_count": len(evidence),
            "question_count": questions,
            "accuracy": (correct / questions * 100) if questions else 0.0,
        }
    completed_goals = sum(
        bool(item.get("completed"))
        for item in state["planner"]["goals"]
    )
    completed_schedule = sum(
        bool(item.get("completed"))
        for item in state["planner"]["schedule"]
    )
    return {
        "learning_round_count": len(learning_rounds),
        "challenge_session_count": len(challenge_results),
        "recovery_session_count": len(recovery_records),
        "question_count": total_questions,
        "correct_count": correct_count,
        "accuracy": (correct_count / total_questions * 100) if total_questions else 0.0,
        "topic_count": len(
            {item.get("topic") for item in rounds if item.get("topic")}
        ),
        "pending_recovery_count": len(pending_recovery_items(state)),
        "challenge_modes": challenge_modes,
        "ai_count": len(state["ai_history"]),
        "planner_goal_count": len(state["planner"]["goals"]),
        "planner_completed_goal_count": completed_goals,
        "planner_schedule_count": len(state["planner"]["schedule"]),
        "planner_completed_schedule_count": completed_schedule,
        "library_resource_count": len(state["library"]["resources"]),
        "library_note_count": len(state["library"]["notes"]),
        "subject_count": len(state["management"]["subjects"]),
    }


def learning_stats(state: dict) -> dict:
    state = normalize_world_state(state)
    rounds = state["rounds"]
    total_questions = sum(max(0, int(item.get("question_count", 0))) for item in rounds)
    correct_count = sum(max(0, int(item.get("correct_count", 0))) for item in rounds)
    completed_recovery = recovery_history(state)
    challenge_results = _challenge_evidence(state)
    study_seconds = sum(
        max(0, int(item.get("duration_seconds", 0)))
        for item in rounds
    ) + sum(
        max(0, int(item.get("duration_seconds", 0)))
        for item in completed_recovery
    )
    completed_goals = sum(
        bool(item.get("completed"))
        for item in state["planner"]["goals"]
    )
    completed_schedule = sum(
        bool(item.get("completed"))
        for item in state["planner"]["schedule"]
    )
    points = (
        correct_count * 10
        + len(rounds) * 20
        + len(completed_recovery) * 15
        + len(challenge_results) * 10
        + len(state["ai_history"]) * 5
        + completed_goals * 10
        + completed_schedule * 10
        + len(state["library"]["notes"]) * 5
        + len(state["management"]["subjects"]) * 3
    )
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
    if challenge_results:
        achievements.append("도전 학습 입문")
    if any(float(item.get("accuracy", 0)) >= 90 for item in challenge_results):
        achievements.append("도전 학습 달인")
    if state["ai_history"]:
        achievements.append("인공지능 학습 연결")
    if state["planner"]["goals"] or state["planner"]["schedule"]:
        achievements.append("학습 계획 수립")
    if state["library"]["notes"]:
        achievements.append("지식 기록자")
    world_records = {
        "Learning": sum(item.get("origin") == "Learning" for item in rounds),
        "Recovery": len(completed_recovery),
        "Challenge": len(challenge_results),
        "Analytics": int(bool(rounds or completed_recovery)),
        "AI": len(state["ai_history"]),
        "Planner": len(state["planner"]["goals"])
        + len(state["planner"]["schedule"]),
        "Library": len(state["library"]["resources"])
        + len(state["library"]["notes"]),
        "Management": len(state["management"]["subjects"]),
        "My Learning": len(state["activity"]),
    }
    return {
        "round_count": len(rounds),
        "learning_round_count": world_records["Learning"],
        "challenge_count": len(challenge_results),
        "question_count": total_questions,
        "correct_count": correct_count,
        "accuracy": (correct_count / total_questions * 100) if total_questions else 0.0,
        "study_seconds": study_seconds,
        "level": level,
        "points": points,
        "achievements": achievements,
        "topic_count": len({item.get("topic") for item in rounds if item.get("topic")}),
        "recovery_count": len(completed_recovery),
        "ai_count": len(state["ai_history"]),
        "planner_goal_count": len(state["planner"]["goals"]),
        "planner_schedule_count": len(state["planner"]["schedule"]),
        "library_count": world_records["Library"],
        "subject_count": len(state["management"]["subjects"]),
        "world_records": world_records,
    }


def build_report(state: dict) -> str:
    stats = learning_stats(state)
    world_analytics = build_world_analytics(state)
    learning_rounds = [
        item for item in state["rounds"] if item.get("origin") == "Learning"
    ]
    recovery_records = recovery_history(state)
    challenge_results = _challenge_evidence(state)
    lines = [
        "# 통합 학습 엔진 학습 보고서",
        "",
        "## 나의 학습",
        f"- 완료 라운드: {stats['round_count']}",
        f"- 학습 주제: {stats['topic_count']}",
        f"- 분석 문항: {stats['question_count']}",
        f"- 전체 정확도: {stats['accuracy']:.1f}%",
        f"- 회복 학습: {stats['recovery_count']}",
        f"- 도전 학습: {stats['challenge_count']}",
        f"- 인공지능 기록: {stats['ai_count']}",
        f"- 학습 계획 목표/일정: {stats['planner_goal_count']}/{stats['planner_schedule_count']}",
        f"- 학습 자료실 기록: {stats['library_count']}",
        f"- 공부시간: {stats['study_seconds'] // 60}분",
        f"- 레벨: {stats['level']}",
        "",
        "## 학습",
    ]
    for item in reversed(learning_rounds[-10:]):
        lines.append(
            f"- {item.get('topic', '-')} / "
            f"{difficulty_label(item.get('difficulty', '-'))} / "
            f"{float(item.get('accuracy', 0)):.1f}%"
        )
    if not learning_rounds:
        lines.append("- 기록 없음")

    lines.extend(["", "## 회복 학습"])
    for item in reversed(recovery_records[-10:]):
        record = item.get("record", {})
        lines.append(
            f"- {', '.join(item.get('topics', [])) or '복습'} / "
            f"{record.get('correct_count', item.get('correct_count', 0))}/"
            f"{record.get('question_count', item.get('question_count', 0))} / "
            f"{float(record.get('accuracy', 0)):.1f}%"
        )
    if not recovery_records:
        lines.append("- 기록 없음")

    lines.extend(["", "## 도전 학습"])
    for item in reversed(challenge_results[-10:]):
        lines.append(
            f"- {challenge_mode_label(item.get('mode', '-'))} / "
            f"{item.get('topic', '-')} / "
            f"{float(item.get('accuracy', 0)):.1f}%"
        )
    if not challenge_results:
        lines.append("- 기록 없음")

    lines.extend(
        [
            "",
            "## 학습 분석",
            f"- 전체 정확도: {world_analytics['accuracy']:.1f}%",
            f"- 분석 문항: {world_analytics['question_count']}",
            f"- 복습 대기: {world_analytics['pending_recovery_count']}",
        ]
    )
    for mode, evidence in world_analytics["challenge_modes"].items():
        lines.append(
            f"- {challenge_mode_label(mode)}: {evidence['session_count']}회 / "
            f"{evidence['accuracy']:.1f}%"
        )

    lines.extend(["", "## 인공지능"])
    for item in reversed(state["ai_history"][-10:]):
        lines.append(
            f"- {item.get('kind', '-')} / {item.get('topic') or '주제 없음'} / "
            f"{_clean_text(item.get('response'), maximum=240)}"
        )
    if not state["ai_history"]:
        lines.append("- 기록 없음")

    lines.extend(["", "## 학습 계획", "### 목표"])
    for item in reversed(state["planner"]["goals"][-10:]):
        lines.append(
            f"- {'완료' if item.get('completed') else '진행 중'} / "
            f"{localized_record_text(item.get('title', '-'))}"
        )
    if not state["planner"]["goals"]:
        lines.append("- 기록 없음")
    lines.append("### 일정")
    for item in reversed(state["planner"]["schedule"][-10:]):
        lines.append(
            f"- {'완료' if item.get('completed') else '예정'} / "
            f"{item.get('scheduled_date', '-')} / "
            f"{world_label(item.get('world', '-'))} / "
            f"{item.get('topic') or '주제 없음'}"
        )
    if not state["planner"]["schedule"]:
        lines.append("- 기록 없음")

    lines.extend(["", "## 학습 자료실"])
    source_counts = {}
    for item in state["library"]["resources"]:
        source = item.get("source_world") or "Learning"
        source_counts[source] = source_counts.get(source, 0) + 1
    for source, count in sorted(source_counts.items()):
        lines.append(f"- {world_label(source)}: {count}개")
    lines.append(f"- 노트: {len(state['library']['notes'])}개")

    settings = state["management"]["settings"]
    lines.extend(
        [
            "",
            "## 관리",
            f"- 과목: {', '.join(state['management']['subjects']) or '없음'}",
            f"- 기본 문제 수: {settings.get('default_question_count', 5)}",
            f"- 기본 난이도: "
            f"{difficulty_label(settings.get('default_difficulty', 'Easy'))}",
            "",
            "## 업적",
        ]
    )
    lines.extend(f"- {item}" for item in stats["achievements"])
    if not stats["achievements"]:
        lines.append("- 기록 없음")
    return "\n".join(lines)
