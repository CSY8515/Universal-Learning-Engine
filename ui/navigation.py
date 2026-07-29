"""Small session-safe primary navigation for the Streamlit application."""


NAVIGATION_OPTIONS = (
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
NAVIGATION_LABELS = {
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


def render_navigation(st_module) -> str:
    """Render a compact navigation control and return the selected view."""

    return st_module.radio(
        "주요 메뉴",
        NAVIGATION_OPTIONS,
        format_func=lambda option: NAVIGATION_LABELS[option],
        horizontal=True,
        key="active_view",
        label_visibility="collapsed",
    )
