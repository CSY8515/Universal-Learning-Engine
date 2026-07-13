"""Pure, session-only Learning Analytics for Universal Learning Engine v0.5.

This module consumes completed v0.4 adaptive summaries. It never changes the
source records, calls OpenAI, persists data, or selects a learning action.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from typing import Iterable


SCHEMA_VERSION = "0.5"
DIFFICULTY_ORDER = ["Easy", "Normal", "Hard", "Nightmare"]
CONFIDENCE_KEYS = ["low", "medium", "high", "unset"]
ANSWER_PATTERN_KEYS = [
    "secure_success",
    "developing_success",
    "uncertain_success",
    "confident_error",
    "developing_gap",
    "recognized_gap",
    "confidence_unknown",
]
MIN_EVIDENCE_ROUNDS = 2
MIN_EVIDENCE_QUESTIONS = 10
STRENGTH_ACCURACY = 85.0
STRENGTH_SUPPORTED_SUCCESS = 60.0
WEAKNESS_ACCURACY = 60.0
WEAKNESS_CONFIDENT_ERROR = 20.0


class AnalyticsRecordError(ValueError):
    """A completed summary cannot safely produce round analytics."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def percentage(count: int | float, total: int | float) -> float:
    """Return a percentage without raising for an empty denominator."""
    return (count / total) * 100 if total else 0.0


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _normalized_counts(
    source: object,
    keys: list[str],
    total: int,
    fallback_key: str,
    issue_prefix: str,
) -> tuple[dict[str, int], list[str]]:
    issues: list[str] = []
    if not isinstance(source, dict):
        counts = {key: 0 for key in keys}
        counts[fallback_key] = total
        return counts, [f"{issue_prefix}_missing"]

    counts: dict[str, int] = {}
    invalid = False
    for key in keys:
        value = source.get(key, 0)
        if not _is_int(value) or value < 0:
            invalid = True
            break
        counts[key] = value

    if invalid or sum(counts.values()) > total:
        counts = {key: 0 for key in keys}
        counts[fallback_key] = total
        return counts, [f"{issue_prefix}_invalid"]

    missing = total - sum(counts.values())
    if missing:
        counts[fallback_key] += missing
        issues.append(f"{issue_prefix}_incomplete")
    return counts, issues


def build_round_analytics(summary: dict, sequence: int) -> dict:
    """Normalize one v0.4 completed summary into the v0.5 round contract."""
    if not isinstance(summary, dict) or not isinstance(summary.get("round_status"), dict):
        raise AnalyticsRecordError("round_status_missing")
    status = summary["round_status"]

    round_id = status.get("round_id")
    topic_key = status.get("topic_key")
    difficulty = status.get("difficulty")
    question_count = status.get("question_count")
    correct_count = status.get("correct_count")
    if not _is_int(round_id):
        raise AnalyticsRecordError("round_id_invalid")
    if not isinstance(topic_key, str) or not topic_key.strip():
        raise AnalyticsRecordError("topic_key_invalid")
    if difficulty not in DIFFICULTY_ORDER:
        raise AnalyticsRecordError("difficulty_invalid")
    if not _is_int(question_count) or question_count <= 0:
        raise AnalyticsRecordError("question_count_invalid")
    if not _is_int(correct_count) or not 0 <= correct_count <= question_count:
        raise AnalyticsRecordError("correct_count_invalid")

    issues: list[str] = []
    wrong_count = question_count - correct_count
    if status.get("wrong_count") != wrong_count:
        issues.append("wrong_count_reconciled")
    accuracy = percentage(correct_count, question_count)
    source_accuracy = status.get("accuracy")
    if not isinstance(source_accuracy, (int, float)) or isinstance(source_accuracy, bool):
        issues.append("accuracy_recalculated")
    elif abs(float(source_accuracy) - accuracy) > 1e-9:
        issues.append("accuracy_recalculated")

    confidence_counts, confidence_issues = _normalized_counts(
        status.get("confidence_counts"),
        CONFIDENCE_KEYS,
        question_count,
        "unset",
        "confidence_counts",
    )
    pattern_counts, pattern_issues = _normalized_counts(
        status.get("answer_patterns"),
        ANSWER_PATTERN_KEYS,
        question_count,
        "confidence_unknown",
        "answer_patterns",
    )
    issues.extend(confidence_issues)
    issues.extend(pattern_issues)

    reported_count = sum(confidence_counts[key] for key in ("low", "medium", "high"))
    supported_success_count = (
        pattern_counts["secure_success"] + pattern_counts["developing_success"]
    )
    confident_error_count = pattern_counts["confident_error"]

    learning_patterns = []
    raw_patterns = summary.get("learning_patterns", [])
    if not isinstance(raw_patterns, list):
        issues.append("learning_patterns_invalid")
    else:
        for signal in raw_patterns:
            if (
                isinstance(signal, dict)
                and isinstance(signal.get("name"), str)
                and signal["name"].strip()
                and isinstance(signal.get("reason"), str)
                and signal["reason"].strip()
            ):
                learning_patterns.append(
                    {"name": signal["name"], "reason": signal["reason"]}
                )
            else:
                issues.append("learning_pattern_item_invalid")

    return {
        "schema_version": SCHEMA_VERSION,
        "round_id": round_id,
        "sequence": sequence,
        "topic_key": topic_key.strip(),
        "difficulty": difficulty,
        "question_count": question_count,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "accuracy": accuracy,
        "confidence": {
            "counts": confidence_counts,
            "percentages": {
                key: percentage(value, question_count)
                for key, value in confidence_counts.items()
            },
            "reported_count": reported_count,
            "reporting_rate": percentage(reported_count, question_count),
        },
        "answer_patterns": {
            "counts": pattern_counts,
            "percentages": {
                key: percentage(value, question_count)
                for key, value in pattern_counts.items()
            },
            "supported_success_count": supported_success_count,
            "supported_success_rate": percentage(
                supported_success_count, question_count
            ),
            "confident_error_count": confident_error_count,
            "confident_error_rate": percentage(confident_error_count, question_count),
        },
        "learning_patterns": learning_patterns,
        "difficulty_recommendation": deepcopy(
            summary.get("difficulty_recommendation")
            if isinstance(summary.get("difficulty_recommendation"), dict)
            else None
        ),
        "recovery_recommendation": deepcopy(
            summary.get("recovery_recommendation")
            if isinstance(summary.get("recovery_recommendation"), dict)
            else None
        ),
        "issues": issues,
    }


def normalize_adaptation_records(adaptation_records: object) -> dict:
    """Normalize valid records independently and report unusable records."""
    result = {"rounds": [], "skipped_record_count": 0, "issues": []}
    if adaptation_records is None:
        return result
    if not isinstance(adaptation_records, dict):
        result["issues"].append("adaptation_records_invalid")
        return result

    for stored_topic, summaries in adaptation_records.items():
        if not isinstance(summaries, list):
            result["issues"].append(f"topic_records_invalid:{stored_topic}")
            continue
        seen_round_ids: set[int] = set()
        for sequence, summary in enumerate(summaries, start=1):
            try:
                round_analytics = build_round_analytics(summary, sequence)
                identity = round_analytics["round_id"]
                if identity in seen_round_ids:
                    raise AnalyticsRecordError("duplicate_round_id")
                seen_round_ids.add(identity)
                if str(stored_topic) != round_analytics["topic_key"]:
                    round_analytics["issues"].append("stored_topic_key_mismatch")
                result["rounds"].append(round_analytics)
            except AnalyticsRecordError as exc:
                result["skipped_record_count"] += 1
                result["issues"].append(
                    f"record_skipped:{stored_topic}:{sequence}:{exc.code}"
                )
    return result


def _direction(change: float | None) -> str:
    if change is None:
        return "not_available"
    if change > 0:
        return "improved"
    if change < 0:
        return "declined"
    return "steady"


def build_aggregate(
    rounds: Iterable[dict], scope: str, scope_key: str | None, ordered: bool = False
) -> dict:
    """Build exact aggregate measures for a selected analytics scope."""
    round_list = list(rounds)
    question_count = sum(item["question_count"] for item in round_list)
    correct_count = sum(item["correct_count"] for item in round_list)
    wrong_count = question_count - correct_count
    accuracies = [item["accuracy"] for item in round_list]

    confidence_counts = Counter({key: 0 for key in CONFIDENCE_KEYS})
    pattern_counts = Counter({key: 0 for key in ANSWER_PATTERN_KEYS})
    signal_frequencies = Counter()
    for item in round_list:
        confidence_counts.update(item["confidence"]["counts"])
        pattern_counts.update(item["answer_patterns"]["counts"])
        signal_frequencies.update(
            {signal["name"] for signal in item["learning_patterns"]}
        )

    reported_count = sum(confidence_counts[key] for key in ("low", "medium", "high"))
    supported_success_count = (
        pattern_counts["secure_success"] + pattern_counts["developing_success"]
    )
    confident_error_count = pattern_counts["confident_error"]

    latest = accuracies[-1] if ordered and accuracies else None
    previous = accuracies[-2] if ordered and len(accuracies) > 1 else None
    latest_change = latest - previous if previous is not None else None
    first_to_latest = (
        latest - accuracies[0] if ordered and len(accuracies) > 1 else None
    )
    repeated_recent_signals: list[str] = []
    if ordered and len(round_list) > 1:
        previous_names = {
            signal["name"] for signal in round_list[-2]["learning_patterns"]
        }
        latest_names = {
            signal["name"] for signal in round_list[-1]["learning_patterns"]
        }
        repeated_recent_signals = sorted(previous_names & latest_names)

    confidence_changes = {
        "reporting_rate_change": None,
        "supported_success_rate_change": None,
        "confident_error_rate_change": None,
    }
    if ordered and len(round_list) > 1:
        first = round_list[0]
        last = round_list[-1]
        confidence_changes = {
            "reporting_rate_change": last["confidence"]["reporting_rate"]
            - first["confidence"]["reporting_rate"],
            "supported_success_rate_change": last["answer_patterns"][
                "supported_success_rate"
            ]
            - first["answer_patterns"]["supported_success_rate"],
            "confident_error_rate_change": last["answer_patterns"][
                "confident_error_rate"
            ]
            - first["answer_patterns"]["confident_error_rate"],
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "scope": scope,
        "scope_key": scope_key,
        "topic_count": len({item["topic_key"] for item in round_list}),
        "round_count": len(round_list),
        "question_count": question_count,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "weighted_accuracy": percentage(correct_count, question_count)
        if question_count
        else None,
        "mean_round_accuracy": sum(accuracies) / len(accuracies)
        if accuracies
        else None,
        "latest_accuracy": latest,
        "previous_accuracy": previous,
        "best_round_accuracy": max(accuracies) if accuracies else None,
        "lowest_round_accuracy": min(accuracies) if accuracies else None,
        "latest_change": latest_change,
        "first_to_latest_change": first_to_latest,
        "accuracy_direction": _direction(latest_change),
        "accuracy_range": max(accuracies) - min(accuracies) if accuracies else None,
        "confidence": {
            "counts": dict(confidence_counts),
            "percentages": {
                key: percentage(value, question_count)
                for key, value in confidence_counts.items()
            },
            "reported_count": reported_count,
            "reporting_rate": percentage(reported_count, question_count),
        },
        "answer_patterns": {
            "counts": dict(pattern_counts),
            "percentages": {
                key: percentage(value, question_count)
                for key, value in pattern_counts.items()
            },
            "supported_success_count": supported_success_count,
            "supported_success_rate": percentage(
                supported_success_count, question_count
            ),
            "confident_error_count": confident_error_count,
            "confident_error_rate": percentage(confident_error_count, question_count),
        },
        "learning_pattern_frequencies": dict(sorted(signal_frequencies.items())),
        "repeated_recent_signals": repeated_recent_signals,
        "confidence_changes": confidence_changes,
        "rounds": round_list,
        "topic_summaries": [],
        "difficulty_summaries": [],
        "strengths": [],
        "weaknesses": [],
        "mixed_evidence": [],
        "insufficient_evidence": [],
        "skipped_record_count": 0,
        "issues": [],
    }


def _evidence_summary(rounds: list[dict]) -> dict:
    aggregate = build_aggregate(
        rounds,
        "topic_difficulty",
        f"{rounds[0]['topic_key']}|{rounds[0]['difficulty']}",
        ordered=True,
    )
    eligible = (
        aggregate["round_count"] >= MIN_EVIDENCE_ROUNDS
        and aggregate["question_count"] >= MIN_EVIDENCE_QUESTIONS
    )
    accuracy = aggregate["weighted_accuracy"]
    supported = aggregate["answer_patterns"]["supported_success_rate"]
    confident_error = aggregate["answer_patterns"]["confident_error_rate"]
    strength = bool(
        eligible
        and accuracy is not None
        and accuracy >= STRENGTH_ACCURACY
        and supported >= STRENGTH_SUPPORTED_SUCCESS
    )
    weakness_rules = []
    if eligible and accuracy is not None and accuracy < WEAKNESS_ACCURACY:
        weakness_rules.append("low_weighted_accuracy")
    if eligible and confident_error >= WEAKNESS_CONFIDENT_ERROR:
        weakness_rules.append("confident_error_evidence")

    if not eligible:
        classification = "insufficient_evidence"
        matched_rules = ["minimum_evidence_not_met"]
    elif strength and weakness_rules:
        classification = "mixed"
        matched_rules = ["strength_thresholds_met", *weakness_rules]
    elif strength:
        classification = "strength"
        matched_rules = ["strength_thresholds_met"]
    elif weakness_rules:
        classification = "weakness"
        matched_rules = weakness_rules
    else:
        classification = "insufficient_evidence"
        matched_rules = ["no_clear_strength_or_weakness"]

    topic_key = rounds[0]["topic_key"]
    difficulty = rounds[0]["difficulty"]
    evidence_text = (
        f"{topic_key} / {difficulty}: {aggregate['round_count']} rounds, "
        f"{aggregate['question_count']} answers, {accuracy:.1f}% weighted accuracy, "
        f"{supported:.1f}% supported success, {confident_error:.1f}% confident errors."
    )
    return {
        "classification": classification,
        "topic_key": topic_key,
        "difficulty": difficulty,
        "round_count": aggregate["round_count"],
        "question_count": aggregate["question_count"],
        "weighted_accuracy": accuracy,
        "supported_success_rate": supported,
        "confident_error_rate": confident_error,
        "matched_rules": matched_rules,
        "evidence_text": evidence_text,
    }


def build_evidence_summaries(rounds: Iterable[dict]) -> dict:
    """Build stable, future-consumable evidence without a Weakness Score."""
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in rounds:
        grouped[(item["topic_key"], item["difficulty"])].append(item)
    all_items = [_evidence_summary(items) for items in grouped.values()]

    strengths = sorted(
        (item for item in all_items if item["classification"] == "strength"),
        key=lambda item: (
            -item["weighted_accuracy"],
            -item["question_count"],
            item["topic_key"],
            DIFFICULTY_ORDER.index(item["difficulty"]),
        ),
    )
    weaknesses = sorted(
        (item for item in all_items if item["classification"] == "weakness"),
        key=lambda item: (
            item["weighted_accuracy"],
            -item["question_count"],
            item["topic_key"],
            DIFFICULTY_ORDER.index(item["difficulty"]),
        ),
    )
    mixed = sorted(
        (item for item in all_items if item["classification"] == "mixed"),
        key=lambda item: (
            item["topic_key"],
            DIFFICULTY_ORDER.index(item["difficulty"]),
        ),
    )
    insufficient = sorted(
        (
            item
            for item in all_items
            if item["classification"] == "insufficient_evidence"
        ),
        key=lambda item: (
            item["topic_key"],
            DIFFICULTY_ORDER.index(item["difficulty"]),
        ),
    )
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "mixed_evidence": mixed,
        "insufficient_evidence": insufficient,
        "concise_strengths": strengths[:3],
        "concise_weaknesses": weaknesses[:3],
    }


def _add_breakdowns(aggregate: dict, rounds: list[dict], include_topics: bool) -> None:
    if include_topics:
        topics = defaultdict(list)
        for item in rounds:
            topics[item["topic_key"]].append(item)
        aggregate["topic_summaries"] = [
            build_aggregate(items, "topic", topic, ordered=True)
            for topic, items in topics.items()
        ]

    difficulties = defaultdict(list)
    for item in rounds:
        difficulties[item["difficulty"]].append(item)
    aggregate["difficulty_summaries"] = [
        build_aggregate(
            difficulties[difficulty],
            "difficulty",
            difficulty,
            ordered=aggregate["scope"] == "current_topic",
        )
        for difficulty in DIFFICULTY_ORDER
        if difficulty in difficulties
    ]

    evidence = build_evidence_summaries(rounds)
    aggregate.update(evidence)


def _learning_summary(aggregate: dict) -> dict:
    if not aggregate["round_count"]:
        return {
            "status": "empty",
            "headline": "No completed learning results are available in this scope.",
            "facts": [],
        }
    facts = [
        f"{aggregate['round_count']} rounds and {aggregate['question_count']} answers",
        f"{aggregate['weighted_accuracy']:.1f}% weighted accuracy",
        f"{aggregate['confidence']['reporting_rate']:.1f}% reported-confidence coverage",
    ]
    if aggregate["accuracy_direction"] != "not_available":
        facts.append(
            f"Latest comparable accuracy direction: {aggregate['accuracy_direction']}"
        )
    return {
        "status": "available",
        "headline": (
            f"{aggregate['correct_count']} of {aggregate['question_count']} answers "
            "were correct in this scope."
        ),
        "facts": facts,
    }


def build_learning_analytics(
    adaptation_records: object, current_topic_key: str | None = None
) -> dict:
    """Build round, current-topic, and overall session-only analytics."""
    normalized = normalize_adaptation_records(adaptation_records)
    rounds = normalized["rounds"]

    overall = build_aggregate(rounds, "overall_session", None, ordered=False)
    overall["skipped_record_count"] = normalized["skipped_record_count"]
    overall["issues"] = list(normalized["issues"])
    _add_breakdowns(overall, rounds, include_topics=True)
    overall["learning_summary"] = _learning_summary(overall)

    current_rounds = (
        [item for item in rounds if item["topic_key"] == current_topic_key]
        if current_topic_key
        else []
    )
    current = build_aggregate(
        current_rounds, "current_topic", current_topic_key, ordered=True
    )
    _add_breakdowns(current, current_rounds, include_topics=False)
    current["learning_summary"] = _learning_summary(current)

    latest_round = current_rounds[-1] if current_rounds else None
    return {
        "schema_version": SCHEMA_VERSION,
        "latest_round": latest_round,
        "current_topic": current,
        "overall": overall,
        "rounds": rounds,
    }
