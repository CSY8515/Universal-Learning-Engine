"""Deterministic, session-only adaptive learning rules for v0.4."""

from __future__ import annotations

from collections import Counter
from typing import Iterable


DIFFICULTY_ORDER = ["Easy", "Normal", "Hard", "Nightmare"]
CONFIDENCE_LEVELS = ["low", "medium", "high"]


def normalize_confidence(value: object) -> str | None:
    """Return a supported confidence value or None for unset/invalid input."""
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    return normalized if normalized in CONFIDENCE_LEVELS else None


def confidence_category(is_correct: bool, confidence: object) -> str:
    """Classify one answer without inferring more than reported evidence."""
    normalized = normalize_confidence(confidence)
    if normalized is None:
        return "confidence_unknown"
    categories = {
        (True, "high"): "secure_success",
        (True, "medium"): "developing_success",
        (True, "low"): "uncertain_success",
        (False, "high"): "confident_error",
        (False, "medium"): "developing_gap",
        (False, "low"): "recognized_gap",
    }
    return categories[(bool(is_correct), normalized)]


def _percentage(count: int, total: int) -> float:
    return (count / total) * 100 if total else 0.0


def build_round_status(
    answers: Iterable[dict], difficulty: str, round_id: int, topic_key: str
) -> dict:
    """Build immutable-by-convention metrics from completed answer evidence."""
    answer_list = [dict(answer) for answer in answers]
    if not answer_list:
        raise ValueError("완료한 라운드에는 답변이 하나 이상 필요합니다.")
    if difficulty not in DIFFICULTY_ORDER:
        raise ValueError("지원하지 않는 난이도입니다.")

    category_counts = Counter()
    confidence_counts = Counter({"low": 0, "medium": 0, "high": 0, "unset": 0})
    correct_count = 0
    for answer in answer_list:
        is_correct = bool(answer.get("is_correct"))
        correct_count += int(is_correct)
        confidence = normalize_confidence(answer.get("confidence"))
        confidence_counts[confidence or "unset"] += 1
        category_counts[confidence_category(is_correct, confidence)] += 1

    total = len(answer_list)
    accuracy = _percentage(correct_count, total)
    return {
        "round_id": round_id,
        "topic_key": topic_key,
        "difficulty": difficulty,
        "question_count": total,
        "correct_count": correct_count,
        "wrong_count": total - correct_count,
        "accuracy": accuracy,
        "confidence_counts": dict(confidence_counts),
        "answer_patterns": dict(category_counts),
    }


def analyze_learning_patterns(status: dict) -> list[dict]:
    """Return deterministic learning signals with supporting evidence."""
    total = status["question_count"]
    accuracy = status["accuracy"]
    patterns = status.get("answer_patterns", {})
    secure_developing = patterns.get("secure_success", 0) + patterns.get(
        "developing_success", 0
    )
    uncertain_unknown = patterns.get("uncertain_success", 0) + patterns.get(
        "confidence_unknown", 0
    )
    confident_errors = patterns.get("confident_error", 0)
    signals = []

    if accuracy >= 85:
        if _percentage(secure_developing, total) >= 60:
            signals.append(
                {
                    "name": "strong_mastery_signal",
                    "reason": "정확도가 85% 이상이고, 안정적이거나 발전 중인 정답이 60% 이상입니다.",
                }
            )
        elif _percentage(uncertain_unknown, total) > 40:
            signals.append(
                {
                    "name": "fragile_success_signal",
                    "reason": "정확도는 85% 이상이지만, 답변의 40%를 넘는 항목에서 확신도 근거가 부족합니다.",
                }
            )
    elif accuracy >= 60:
        signals.append(
            {
                "name": "developing_understanding",
                "reason": "정확도가 60% 이상 85% 미만입니다.",
            }
        )
    else:
        signals.append(
            {
                "name": "foundational_gap_signal",
                "reason": "현재 난이도에서 정확도가 60% 미만입니다.",
            }
        )

    if _percentage(confident_errors, total) >= 20:
        signals.append(
            {
                "name": "overconfidence_risk",
                "reason": "높은 확신도로 답했지만 틀린 문항이 전체의 20% 이상입니다.",
            }
        )
    return signals


def recommend_difficulty(status: dict) -> dict:
    """Recommend a bounded next difficulty; never apply it automatically."""
    current = status["difficulty"]
    if current not in DIFFICULTY_ORDER:
        raise ValueError("지원하지 않는 난이도입니다.")
    total = status["question_count"]
    accuracy = status["accuracy"]
    confidence = status.get("confidence_counts", {})
    medium_high = confidence.get("medium", 0) + confidence.get("high", 0)
    low_unset = confidence.get("low", 0) + confidence.get("unset", 0)
    current_index = DIFFICULTY_ORDER.index(current)

    if accuracy >= 85 and _percentage(medium_high, total) >= 60:
        recommended_index = min(current_index + 1, len(DIFFICULTY_ORDER) - 1)
        rule = "high_accuracy_supported_confidence"
        reason = "정확도가 85% 이상이고 답변의 60% 이상에서 보통 이상의 확신도를 선택했습니다."
    elif accuracy >= 85 and _percentage(low_unset, total) > 40:
        recommended_index = current_index
        rule = "high_accuracy_limited_confidence"
        reason = "정확도는 85% 이상이지만 답변의 40%를 넘는 항목에서 확신도가 낮거나 선택되지 않았습니다."
    elif accuracy >= 60:
        recommended_index = current_index
        rule = "developing_accuracy"
        reason = "정확도가 60% 이상 85% 미만이므로 현재 난이도를 유지합니다."
    else:
        recommended_index = max(current_index - 1, 0)
        rule = "low_accuracy"
        reason = "정확도가 60% 미만이므로 한 단계 낮은 난이도를 추천합니다."

    recommended = DIFFICULTY_ORDER[recommended_index]
    if recommended == current and current_index in (0, len(DIFFICULTY_ORDER) - 1):
        reason += " 지원하는 난이도 범위 안에서 현재 단계를 유지합니다."
    return {
        "current_difficulty": current,
        "recommended_difficulty": recommended,
        "rule": rule,
        "reason": reason,
        "accuracy": accuracy,
        "advisory": "추천은 자동 적용되지 않으며 사용자가 직접 선택할 수 있습니다.",
    }


def recommend_recovery(status: dict, signals: list[dict]) -> dict:
    """Return advisory recovery priority and relative interval wording."""
    names = {signal["name"] for signal in signals}
    if status["accuracy"] < 60 or "overconfidence_risk" in names:
        priority = "high"
        interval = "다음 라운드 전에 복습하세요."
        reason = "낮은 정확도 또는 확신한 오답 근거가 있어 바로 복습하는 것이 좋습니다."
    elif status["accuracy"] < 85 or "fragile_success_signal" in names:
        priority = "medium"
        interval = "현재 학습 중에 다시 복습하세요."
        reason = "성과가 고르지 않거나 확신도 근거가 부족해 학습 내용을 다질 필요가 있습니다."
    else:
        priority = "low"
        interval = "바로 복습할 필요는 없습니다."
        reason = "현재 라운드에서 과신 위험 없이 충분한 숙달 신호가 확인됐습니다."
    return {
        "priority": priority,
        "interval": interval,
        "reason": reason,
        "advisory": "알림이나 자동 일정은 생성되지 않았습니다.",
    }


def build_adaptive_summary(status: dict) -> dict:
    """Produce all deterministic v0.4 recommendations for one completed round."""
    signals = analyze_learning_patterns(status)
    return {
        "round_status": dict(status),
        "learning_patterns": signals,
        "difficulty_recommendation": recommend_difficulty(status),
        "recovery_recommendation": recommend_recovery(status, signals),
    }
