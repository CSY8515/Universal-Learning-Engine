"""Presentation helpers for the integrated learning engine interface."""

from .navigation import HOME_VIEW, NAVIGATION_OPTIONS, render_navigation
from .contracts import UI_FOUNDATION_INTERFACE_VERSION
from .interface import (
    UICompatibilityLayer,
    UltraBrainUIInterface,
    get_ui_compatibility_layer,
)
from .theme import apply_official_theme, render_world_stage

__all__ = [
    "HOME_VIEW",
    "NAVIGATION_OPTIONS",
    "UI_FOUNDATION_INTERFACE_VERSION",
    "UICompatibilityLayer",
    "UltraBrainUIInterface",
    "apply_official_theme",
    "get_ui_compatibility_layer",
    "render_navigation",
    "render_world_stage",
]
