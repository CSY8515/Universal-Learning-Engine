"""Session-safe navigation for the official Universal Learning World."""


HOME_VIEW = "World Map"
NAVIGATION_OPTIONS = (
    HOME_VIEW,
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
    HOME_VIEW: "학습 세계",
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
HOME_DOCK_OPTIONS = (
    HOME_VIEW,
    "Learning",
    "Planner",
    "Analytics",
    "AI",
)
HOME_DOCK_LABELS = {
    HOME_VIEW: "학습 세계",
    "Learning": "학습",
    "Planner": "오늘",
    "Analytics": "리포트",
    "AI": "인공지능",
}


def render_navigation(st_module) -> str:
    """Render the orbital map or compact World dock."""

    is_world_map = st_module.session_state.get("active_view") == HOME_VIEW
    container_key = (
        "ule_world_map_navigation"
        if is_world_map
        else "ule_world_dock"
    )

    with st_module.container(key=container_key):
        if is_world_map:
            st_module.markdown(
                """
                <div class="ule-map-copy">
                  <h1>Universal Learning Engine</h1>
                  <span class="ule-map-copy__hint">주변의 세계를 선택하세요</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        selected_view = st_module.radio(
            "주요 메뉴",
            NAVIGATION_OPTIONS,
            format_func=lambda option: NAVIGATION_LABELS[option],
            horizontal=True,
            key="active_view",
            label_visibility="collapsed",
        )

    if is_world_map:
        if st_module.session_state.get("ule_home_dock_view") != HOME_VIEW:
            st_module.session_state.ule_home_dock_view = HOME_VIEW

        def sync_home_dock() -> None:
            st_module.session_state.active_view = (
                st_module.session_state.ule_home_dock_view
            )

        with st_module.container(key="ule_home_dock"):
            st_module.radio(
                "학습 세계 빠른 이동",
                HOME_DOCK_OPTIONS,
                format_func=lambda option: HOME_DOCK_LABELS[option],
                horizontal=True,
                key="ule_home_dock_view",
                on_change=sync_home_dock,
                label_visibility="collapsed",
            )

    return selected_view
