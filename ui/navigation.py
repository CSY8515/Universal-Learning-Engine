"""Small session-safe primary navigation for the Streamlit application."""


NAVIGATION_OPTIONS = ("Dashboard", "Learning", "Review")


def render_navigation(st_module, *, on_change=None) -> str:
    """Render a compact navigation control and return the selected view."""

    return st_module.radio(
        "Primary navigation",
        NAVIGATION_OPTIONS,
        horizontal=True,
        key="active_view",
        label_visibility="collapsed",
        on_change=on_change,
    )
