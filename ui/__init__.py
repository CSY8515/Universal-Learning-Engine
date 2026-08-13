"""Presentation helpers for the integrated learning engine interface."""

from .navigation import HOME_VIEW, NAVIGATION_OPTIONS, render_navigation
from .contracts import UI_FOUNDATION_INTERFACE_VERSION
from .interface import (
    UICompatibilityLayer,
    UltraBrainUIInterface,
    get_ui_compatibility_layer,
)
from .theme import (
    APPLIED_QUERY_CONTRACT_SESSION_KEY,
    apply_official_theme,
    query_adjustment_css,
    query_contract_from_mapping,
    render_world_stage,
    resolve_applied_query_contract,
    resolve_theme_world,
    theme_settings_from_mapping,
)
from .propagation import InheritedTheme, THEME_KEYS, resolve_inherited_theme

__all__ = [
    "HOME_VIEW",
    "NAVIGATION_OPTIONS",
    "UI_FOUNDATION_INTERFACE_VERSION",
    "UICompatibilityLayer",
    "UltraBrainUIInterface",
    "APPLIED_QUERY_CONTRACT_SESSION_KEY",
    "InheritedTheme",
    "THEME_KEYS",
    "apply_official_theme",
    "query_adjustment_css",
    "query_contract_from_mapping",
    "resolve_applied_query_contract",
    "resolve_theme_world",
    "theme_settings_from_mapping",
    "get_ui_compatibility_layer",
    "render_navigation",
    "render_world_stage",
    "resolve_inherited_theme",
]
