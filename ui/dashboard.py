"""Session-only Dashboard built from existing learning evidence."""

from __future__ import annotations

from .components import (
    format_percentage,
    format_priority,
    render_empty_state,
    render_view_intro,
)


def _all_records(adaptation_records: object) -> list[dict]:
    if not isinstance(adaptation_records, dict):
        return []
    records: list[dict] = []
    for topic_records in adaptation_records.values():
        if isinstance(topic_records, list):
            records.extend(item for item in topic_records if isinstance(item, dict))
    return records


def _latest_summary(adaptation_records: object, latest_summary: object) -> dict | None:
    if isinstance(latest_summary, dict):
        return latest_summary
    records = _all_records(adaptation_records)
    return records[-1] if records else None


def _recommendation(summary: dict | None) -> tuple[str, str]:
    if not summary:
        return "Start a learning session", "Choose a topic and create your first lesson."
    difficulty = summary.get("difficulty_recommendation")
    if isinstance(difficulty, dict):
        current = difficulty.get("current_difficulty", "current level")
        recommended = difficulty.get("recommended_difficulty", current)
        title = (
            f"Continue at {current}"
            if recommended == current
            else f"Try {recommended} next"
        )
        reason = difficulty.get("reason")
        if isinstance(reason, str) and reason.strip():
            return title, reason
        return title, "Review the latest evidence before starting the next round."
    return "Review the latest round", "Use the completed result to plan the next session."


def render_dashboard(
    st_module,
    *,
    lesson: object,
    adaptation_records: object,
    latest_summary: object,
    analytics_result: object = None,
) -> None:
    """Render a compact Dashboard without changing source evidence."""

    render_view_intro(
        st_module,
        "Today's Learning",
        "Dashboard",
        "Your current session, recent evidence, and next learning action in one place.",
    )

    safe_lesson = lesson if isinstance(lesson, dict) else None
    summary = _latest_summary(adaptation_records, latest_summary)
    status = summary.get("round_status", {}) if summary else {}
    recovery = summary.get("recovery_recommendation", {}) if summary else {}
    progress = summary.get("learning_progress", {}) if summary else {}
    recommendation, recommendation_reason = _recommendation(summary)

    current_topic = safe_lesson.get("topic") if safe_lesson else None
    if not current_topic and isinstance(status, dict):
        current_topic = status.get("topic_key")

    with st_module.container(border=True):
        st_module.caption("CURRENT TOPIC")
        st_module.subheader(current_topic or "No active topic")
        if safe_lesson:
            difficulty = safe_lesson.get("difficulty", "Easy")
            count = safe_lesson.get(
                "requested_question_count", len(safe_lesson.get("cbt", []))
            )
            st_module.write(f"{difficulty} / {count} CBT questions")
        else:
            st_module.write("Open Learning below to create a lesson for any topic.")

    st_module.subheader("Recommended Next Step")
    with st_module.container(border=True):
        st_module.markdown(f"**{recommendation}**")
        st_module.write(recommendation_reason)
        st_module.caption(
            "Evidence-based session guidance. Nothing is started automatically."
        )

    accuracy = status.get("accuracy") if isinstance(status, dict) else None
    recovery_priority = recovery.get("priority") if isinstance(recovery, dict) else None
    completed_rounds = progress.get("completed_rounds") if isinstance(progress, dict) else None
    metric_columns = st_module.columns(3)
    metric_columns[0].metric("Accuracy", format_percentage(accuracy))
    metric_columns[1].metric("Recovery Priority", format_priority(recovery_priority))
    metric_columns[2].metric("Learning Progress", completed_rounds or 0)

    recent_columns = st_module.columns(2)
    with recent_columns[0]:
        st_module.subheader("Recent Round")
        if summary and isinstance(status, dict):
            correct = status.get("correct_count", 0)
            questions = status.get("question_count", 0)
            difficulty = status.get("difficulty", "-")
            st_module.write(f"{correct} / {questions} correct / {difficulty}")
        else:
            render_empty_state(
                st_module,
                "No completed round",
                "Results will appear after CBT completion.",
            )

    with recent_columns[1]:
        st_module.subheader("Weakness Summary")
        weaknesses = []
        if isinstance(analytics_result, dict):
            overall = analytics_result.get("overall", {})
            if isinstance(overall, dict):
                weaknesses = overall.get("concise_weaknesses", [])
        if weaknesses:
            for item in weaknesses[:3]:
                if isinstance(item, dict):
                    st_module.write(
                        f"- {item.get('topic_key', 'Topic')} / "
                        f"{item.get('difficulty', '-')} / "
                        f"{format_percentage(item.get('weighted_accuracy'))}"
                    )
        else:
            st_module.write("No evidence-qualified weakness is available yet.")

    st_module.subheader("Recent Activity")
    records = _all_records(adaptation_records)
    if not records:
        st_module.write("No completed activity in this session.")
    else:
        for item in reversed(records[-3:]):
            item_status = item.get("round_status", {})
            if isinstance(item_status, dict):
                st_module.write(
                    f"- {item_status.get('topic_key', 'topic')} / "
                    f"{item_status.get('difficulty', '-')} / "
                    f"{format_percentage(item_status.get('accuracy'))} accuracy"
                )

    st_module.caption(
        "Dashboard data exists only in this Streamlit session. "
        "Home reset clears retained learning evidence."
    )
