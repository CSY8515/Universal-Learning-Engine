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
        raise ValueError("A completed round requires at least one answer.")
    if difficulty not in DIFFICULTY_ORDER:
        raise ValueError("Unsupported difficulty.")

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
                    "reason": "At least 85% correct with at least 60% secure or developing success.",
                }
            )
        elif _percentage(uncertain_unknown, total) > 40:
            signals.append(
                {
                    "name": "fragile_success_signal",
                    "reason": "At least 85% correct, but confidence evidence is limited for more than 40% of answers.",
                }
            )
    elif accuracy >= 60:
        signals.append(
            {
                "name": "developing_understanding",
                "reason": "Accuracy is between 60% and 84%.",
            }
        )
    else:
        signals.append(
            {
                "name": "foundational_gap_signal",
                "reason": "Accuracy is below 60% at the current difficulty.",
            }
        )

    if _percentage(confident_errors, total) >= 20:
        signals.append(
            {
                "name": "overconfidence_risk",
                "reason": "At least 20% of answers were incorrect with high reported confidence.",
            }
        )
    return signals


def recommend_difficulty(status: dict) -> dict:
    """Recommend a bounded next difficulty; never apply it automatically."""
    current = status["difficulty"]
    if current not in DIFFICULTY_ORDER:
        raise ValueError("Unsupported difficulty.")
    total = status["question_count"]
    accuracy = status["accuracy"]
    confidence = status.get("confidence_counts", {})
    medium_high = confidence.get("medium", 0) + confidence.get("high", 0)
    low_unset = confidence.get("low", 0) + confidence.get("unset", 0)
    current_index = DIFFICULTY_ORDER.index(current)

    if accuracy >= 85 and _percentage(medium_high, total) >= 60:
        recommended_index = min(current_index + 1, len(DIFFICULTY_ORDER) - 1)
        rule = "high_accuracy_supported_confidence"
        reason = "Accuracy is at least 85% and at least 60% of answers report medium or high confidence."
    elif accuracy >= 85 and _percentage(low_unset, total) > 40:
        recommended_index = current_index
        rule = "high_accuracy_limited_confidence"
        reason = "Accuracy is at least 85%, but confidence is low or unset for more than 40% of answers."
    elif accuracy >= 60:
        recommended_index = current_index
        rule = "developing_accuracy"
        reason = "Accuracy is between 60% and 84%, so the current difficulty is maintained."
    else:
        recommended_index = max(current_index - 1, 0)
        rule = "low_accuracy"
        reason = "Accuracy is below 60%, so one lower difficulty is recommended."

    recommended = DIFFICULTY_ORDER[recommended_index]
    if recommended == current and current_index in (0, len(DIFFICULTY_ORDER) - 1):
        reason += " The recommendation remains within the supported difficulty range."
    return {
        "current_difficulty": current,
        "recommended_difficulty": recommended,
        "rule": rule,
        "reason": reason,
        "accuracy": accuracy,
        "advisory": "You remain in control; this recommendation is not applied automatically.",
    }


def recommend_recovery(status: dict, signals: list[dict]) -> dict:
    """Return advisory recovery priority and relative interval wording."""
    names = {signal["name"] for signal in signals}
    if status["accuracy"] < 60 or "overconfidence_risk" in names:
        priority = "high"
        interval = "Review before the next round."
        reason = "Low accuracy or confident-error evidence indicates immediate recovery value."
    elif status["accuracy"] < 85 or "fragile_success_signal" in names:
        priority = "medium"
        interval = "Review later in the current session."
        reason = "Mixed performance or limited confidence evidence suggests consolidation."
    else:
        priority = "low"
        interval = "No immediate recovery needed."
        reason = "Current-round results show a strong mastery signal without overconfidence risk."
    return {
        "priority": priority,
        "interval": interval,
        "reason": reason,
        "advisory": "No reminder or background schedule has been created.",
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
