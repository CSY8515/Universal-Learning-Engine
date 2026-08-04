"""Versioned contracts for Ultra Brain UI compatibility.

The contracts in this module describe presentation settings only.  They do not
own learner data, Streamlit state, navigation, or business logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field


UI_FOUNDATION_INTERFACE_VERSION = "1.0"


@dataclass(frozen=True)
class ColorTokens:
    """Semantic color palette consumed by every ULE screen."""

    background: str = "#02060b"
    background_alt: str = "#06101c"
    surface: str = "rgba(5, 16, 27, 0.74)"
    surface_strong: str = "rgba(4, 12, 21, 0.9)"
    text: str = "#f4f7fb"
    muted: str = "#a9b6c5"
    accent: str = "#58a7ff"
    accent_secondary: str = "#8ad8ff"
    border: str = "rgba(133, 188, 255, 0.24)"
    border_accent: str = "rgba(221, 181, 91, 0.42)"
    focus: str = "rgba(110, 186, 255, 0.72)"
    gold: str = "#e1bd6b"
    gold_soft: str = "#a88442"
    success: str = "#79d8b0"
    warning: str = "#e1bd6b"
    error: str = "#ff8f9b"


@dataclass(frozen=True)
class TypographyTokens:
    """Font and text-scale tokens."""

    body: str = '"Pretendard", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif'
    display: str = '"Batang", "Nanum Myeongjo", serif'
    monospace: str = '"Cascadia Code", Consolas, monospace'
    base_size: str = "16px"
    heading_weight: str = "700"


@dataclass(frozen=True)
class IconTokens:
    """Icon presentation tokens independent of icon content."""

    color: str = "#f4f7fb"
    accent: str = "#bddcff"
    size: str = "1.08rem"
    family: str = '"Segoe UI Symbol", sans-serif'


@dataclass(frozen=True)
class SurfaceTokens:
    """Card and glass-surface tokens."""

    card_background: str = "linear-gradient(135deg, rgba(13, 31, 46, 0.8), rgba(2, 9, 17, 0.72)), rgba(4, 13, 23, 0.72)"
    card_border: str = "rgba(133, 188, 255, 0.24)"
    card_radius: str = "1.35rem"
    card_shadow: str = "0 24px 80px rgba(0, 0, 0, 0.55)"
    card_hover_shadow: str = "0 18px 48px rgba(19, 101, 187, 0.24)"
    glass_blur: str = "22px"
    dock_blur: str = "20px"
    scene_border: str = "rgba(129, 177, 236, 0.18)"
    scene_radius: str = "1.5rem"
    home_dock_background: str = "linear-gradient(180deg, rgba(7, 22, 43, 0.9), rgba(1, 7, 16, 0.94))"
    home_dock_border: str = "rgba(112, 174, 246, 0.32)"
    home_dock_radius: str = "1.5rem"
    world_dock_background: str = "linear-gradient(180deg, rgba(10, 24, 40, 0.84), rgba(2, 9, 17, 0.9)), rgba(2, 9, 17, 0.84)"
    world_dock_border: str = "rgba(135, 184, 236, 0.24)"
    world_dock_radius: str = "1.2rem"
    world_dock_item_radius: str = "0.8rem"


@dataclass(frozen=True)
class ButtonTokens:
    """Button state tokens shared by Streamlit and trusted HTML controls."""

    background: str = "linear-gradient(180deg, rgba(16, 43, 72, 0.88), rgba(4, 16, 30, 0.92))"
    primary_background: str = "linear-gradient(180deg, rgba(34, 98, 170, 0.94), rgba(6, 34, 70, 0.96))"
    text: str = "#edf5ff"
    border: str = "rgba(120, 181, 246, 0.32)"
    radius: str = "999px"
    shadow: str = "inset 0 0 18px rgba(68, 138, 231, 0.12)"
    hint_background: str = "linear-gradient(180deg, rgba(8, 32, 61, 0.88), rgba(2, 10, 22, 0.88))"
    hint_border: str = "rgba(103, 178, 255, 0.58)"
    hint_text: str = "#f5f9ff"
    orbit_background: str = "rgba(2, 8, 15, 0.78)"
    orbit_border: str = "rgba(215, 181, 98, 0.42)"
    orbit_text: str = "rgba(244, 248, 255, 0.86)"


@dataclass(frozen=True)
class LayoutTokens:
    """Global layout constraints; values remain CSS-native for host control."""

    app_max_width: str = "1640px"
    scene_max_width: str = "1600px"
    content_padding: str = "1rem 1.25rem 7.5rem"
    home_dock_max_width: str = "50rem"
    world_dock_max_width: str = "1040px"
    gap: str = "1rem"


@dataclass(frozen=True)
class WidgetTokens:
    """Form, metric, dialog, and dashboard surface tokens."""

    background: str = "rgba(3, 12, 21, 0.48)"
    border: str = "rgba(130, 178, 230, 0.18)"
    radius: str = "1rem"
    shadow: str = "inset 0 1px 0 rgba(255, 255, 255, 0.035)"
    input_background: str = "rgba(1, 8, 15, 0.72)"
    input_border: str = "rgba(136, 184, 237, 0.26)"
    dialog_background: str = "rgba(3, 12, 21, 0.96)"
    dashboard_background: str = "rgba(3, 12, 21, 0.72)"
    metric_background: str = "radial-gradient(circle at 85% 15%, rgba(65, 139, 232, 0.16), transparent 40%), rgba(4, 15, 26, 0.68)"
    metric_border: str = "rgba(135, 183, 233, 0.18)"
    tab_background: str = "rgba(2, 9, 17, 0.46)"
    tab_border: str = "rgba(131, 180, 232, 0.14)"


@dataclass(frozen=True)
class AnimationTokens:
    """Motion timings and easing shared by every World."""

    enabled: bool = True
    fast: str = "180ms"
    normal: str = "320ms"
    label: str = "260ms"
    slow: str = "900ms"
    world_reveal: str = "1.05s"
    panel: str = "650ms"
    content: str = "700ms"
    dock: str = "600ms"
    easing: str = "cubic-bezier(0.2, 0.8, 0.2, 1)"


@dataclass(frozen=True)
class BackgroundTokens:
    """Background resources for the map and nine functional Worlds."""

    world_map: str = 'url("./app/static/worlds/world-map.png")'
    w01: str = 'url("./app/static/worlds/w01.png")'
    w02: str = 'url("./app/static/worlds/w02.png")'
    w03: str = 'url("./app/static/worlds/w03.png")'
    w04: str = 'url("./app/static/worlds/w04.png")'
    w05: str = 'url("./app/static/worlds/w05.png")'
    w06: str = 'url("./app/static/worlds/w06.png")'
    w07: str = 'url("./app/static/worlds/w07.png")'
    w08: str = 'url("./app/static/worlds/w08.png")'
    w09: str = 'url("./app/static/worlds/w09.png")'


@dataclass(frozen=True)
class DesignTokens:
    """Complete presentation token set accepted from the Ultra Brain host."""

    mode: str = "dark"
    colors: ColorTokens = field(default_factory=ColorTokens)
    typography: TypographyTokens = field(default_factory=TypographyTokens)
    icons: IconTokens = field(default_factory=IconTokens)
    surfaces: SurfaceTokens = field(default_factory=SurfaceTokens)
    buttons: ButtonTokens = field(default_factory=ButtonTokens)
    layout: LayoutTokens = field(default_factory=LayoutTokens)
    widgets: WidgetTokens = field(default_factory=WidgetTokens)
    animation: AnimationTokens = field(default_factory=AnimationTokens)
    backgrounds: BackgroundTokens = field(default_factory=BackgroundTokens)


@dataclass(frozen=True)
class ThemeContract:
    """Versioned theme payload exposed through the compatibility interface."""

    theme_id: str
    interface_version: str
    tokens: DesignTokens


@dataclass(frozen=True)
class ComponentContract:
    """Token dependencies for one reusable UI component family."""

    component_id: str
    required_tokens: tuple[str, ...]


@dataclass(frozen=True)
class ModuleThemeContract:
    """Theme dependencies for one application module or World."""

    module_id: str
    background_token: str
    components: tuple[str, ...]
