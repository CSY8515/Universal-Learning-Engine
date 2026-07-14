"""Review-screen helpers that reuse existing result and analytics renderers."""

from .components import render_empty_state, render_view_intro


def render_review_intro(st_module, has_completed_round: bool) -> bool:
    render_view_intro(
        st_module,
        "Learning Evidence",
        "Review",
        "Revisit your completed round, explanations, recommendation, and session analytics.",
    )
    if has_completed_round:
        return True
    render_empty_state(
        st_module,
        "Nothing to review yet",
        "Complete a CBT round to unlock the review workspace.",
    )
    return False
