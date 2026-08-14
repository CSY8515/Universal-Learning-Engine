"""Session-safe navigation for the official Universal Learning World."""

from html import escape


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
    HOME_VIEW: "홈",
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
    HOME_VIEW: "홈",
    "Learning": "학습",
    "Planner": "오늘",
    "Analytics": "리포트",
    "AI": "인공지능",
}


def render_navigation(st_module, theme_world="official") -> str:
    """Render the orbital map or compact World dock."""

    theme_id = escape(str(getattr(theme_world, "theme_id", theme_world)), quote=True)
    source_world_id = escape(
        str(getattr(theme_world, "source_world_id", "")), quote=True
    )
    revision = int(getattr(theme_world, "revision", 1))
    visual_theme_id = escape(
        str(getattr(theme_world, "visual_theme_id", theme_id)), quote=True
    )
    asset_state = escape(
        str(getattr(theme_world, "asset_state", "official")), quote=True
    )
    asset_required = str(
        bool(getattr(theme_world, "theme_asset_required", False))
    ).lower()
    home_asset = str(getattr(theme_world, "home_asset", ""))
    central_asset = str(getattr(theme_world, "central_asset", ""))
    navigation_skin_asset = str(
        getattr(theme_world, "navigation_skin_asset", "")
    )
    role_assets_active = (
        asset_state == "theme-project-role"
        and bool(home_asset)
        and bool(central_asset)
        and bool(navigation_skin_asset)
    )
    is_world_map = st_module.session_state.get("active_view") == HOME_VIEW
    container_key = (
        "ule_world_map_navigation"
        if is_world_map
        else "ule_world_dock"
    )

    with st_module.container(key=container_key):
        role_asset_style = ""
        if is_world_map and role_assets_active:
            home_url = escape(f"./app/static/{home_asset}", quote=True)
            central_url = escape(f"./app/static/{central_asset}", quote=True)
            navigation_url = escape(
                f"./app/static/{navigation_skin_asset}", quote=True
            )
            role_asset_style = (
                '<style data-ule-role-assets="true">'
                '.st-key-ule_world_map_navigation:has(.ule-theme-context[data-theme-role-assets="true"]){'
                f"--ule-active-theme-image:url('{home_url}');"
                f"--ule-home-detail-image:url('{central_url}');"
                "--ule-home-detail-size:contain;"
                f"--ule-navigation-skin:url('{navigation_url}');"
                '}</style>'
            )
        st_module.markdown(
            (
                role_asset_style
                + f'<span class="ule-theme-context" data-theme-world="{theme_id}" '
                f'data-theme-visual="{visual_theme_id}" '
                f'data-theme-asset-state="{asset_state}" '
                f'data-theme-asset-required="{asset_required}" '
                f'data-theme-role-assets="{str(role_assets_active).lower()}" '
                f'data-theme-source-world="{source_world_id}" '
                f'data-theme-revision="{revision}" hidden></span>'
            ),
            unsafe_allow_html=True,
        )
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
                "빠른 이동",
                HOME_DOCK_OPTIONS,
                format_func=lambda option: HOME_DOCK_LABELS[option],
                horizontal=True,
                key="ule_home_dock_view",
                on_change=sync_home_dock,
                label_visibility="collapsed",
            )

    return selected_view
