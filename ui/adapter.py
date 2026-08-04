"""Validated Ultra Brain theme adapter and CSS compatibility mapping."""

from __future__ import annotations

from dataclasses import fields, replace
import re
from typing import Any, Mapping

from .contracts import (
    AnimationTokens,
    BackgroundTokens,
    ButtonTokens,
    ColorTokens,
    DesignTokens,
    IconTokens,
    LayoutTokens,
    SurfaceTokens,
    ThemeContract,
    TypographyTokens,
    UI_FOUNDATION_INTERFACE_VERSION,
    WidgetTokens,
)


class ThemeContractError(ValueError):
    """Raised when a host sends an unsupported or unsafe theme payload."""


_GROUP_TYPES = {
    "colors": ColorTokens,
    "typography": TypographyTokens,
    "icons": IconTokens,
    "surfaces": SurfaceTokens,
    "buttons": ButtonTokens,
    "layout": LayoutTokens,
    "widgets": WidgetTokens,
    "animation": AnimationTokens,
    "backgrounds": BackgroundTokens,
}
_UNSAFE_CSS_FRAGMENTS = (
    "</style",
    "<script",
    "javascript:",
    "expression(",
    "@import",
    "{",
    "}",
    ";",
)


def _safe_css_value(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ThemeContractError(f"{name} must be a non-empty CSS string")
    cleaned = value.strip()
    if len(cleaned) > 600:
        raise ThemeContractError(f"{name} exceeds the compatibility limit")
    lowered = cleaned.casefold()
    if any(fragment in lowered for fragment in _UNSAFE_CSS_FRAGMENTS):
        raise ThemeContractError(f"{name} contains an unsafe CSS fragment")
    return cleaned


def _safe_theme_id(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", value
    ):
        raise ThemeContractError("theme_id must be a safe registry identifier")
    return value


class ThemeAdapter:
    """Translate a versioned Ultra Brain mapping into ULE design tokens."""

    def __init__(self, default_theme: ThemeContract | None = None) -> None:
        self.default_theme = default_theme or ThemeContract(
            theme_id="ule-official",
            interface_version=UI_FOUNDATION_INTERFACE_VERSION,
            tokens=DesignTokens(),
        )

    def adapt(self, settings: Mapping[str, Any] | None = None) -> ThemeContract:
        """Validate and merge host settings without mutating the default theme."""

        if settings is None:
            return self.default_theme
        if not isinstance(settings, Mapping):
            raise ThemeContractError("theme settings must be a mapping")

        allowed = {"theme_id", "interface_version", "mode", *_GROUP_TYPES}
        unknown = sorted(set(settings) - allowed)
        if unknown:
            raise ThemeContractError(f"unsupported theme fields: {', '.join(unknown)}")

        interface_version = settings.get(
            "interface_version", self.default_theme.interface_version
        )
        if interface_version != UI_FOUNDATION_INTERFACE_VERSION:
            raise ThemeContractError(
                f"unsupported theme interface version: {interface_version}"
            )

        theme_id = _safe_theme_id(
            settings.get("theme_id", self.default_theme.theme_id)
        )
        mode = settings.get("mode", self.default_theme.tokens.mode)
        if mode not in {"dark", "light", "system"}:
            raise ThemeContractError("mode must be dark, light, or system")

        tokens = replace(self.default_theme.tokens, mode=mode)
        for group_name, group_type in _GROUP_TYPES.items():
            updates = settings.get(group_name)
            if updates is None:
                continue
            if not isinstance(updates, Mapping):
                raise ThemeContractError(f"{group_name} must be a mapping")
            allowed_fields = {item.name for item in fields(group_type)}
            unknown_fields = sorted(set(updates) - allowed_fields)
            if unknown_fields:
                raise ThemeContractError(
                    f"unsupported {group_name} fields: {', '.join(unknown_fields)}"
                )
            current_group = getattr(tokens, group_name)
            safe_updates: dict[str, str | bool] = {}
            for key, value in updates.items():
                current_value = getattr(current_group, key)
                if isinstance(current_value, bool):
                    if not isinstance(value, bool):
                        raise ThemeContractError(
                            f"{group_name}.{key} must be a boolean"
                        )
                    safe_updates[key] = value
                else:
                    safe_updates[key] = _safe_css_value(
                        f"{group_name}.{key}", value
                    )
            tokens = replace(
                tokens,
                **{group_name: replace(current_group, **safe_updates)},
            )

        return ThemeContract(
            theme_id=str(theme_id),
            interface_version=UI_FOUNDATION_INTERFACE_VERSION,
            tokens=tokens,
        )

    @staticmethod
    def css_variables(theme: ThemeContract) -> dict[str, str]:
        """Return the closed CSS-variable set consumed by repository CSS."""

        t = theme.tokens
        animation_fast = t.animation.fast if t.animation.enabled else "0.01ms"
        animation_normal = t.animation.normal if t.animation.enabled else "0.01ms"
        animation_label = t.animation.label if t.animation.enabled else "0.01ms"
        animation_slow = t.animation.slow if t.animation.enabled else "0.01ms"
        animation_world_reveal = (
            t.animation.world_reveal if t.animation.enabled else "0.01ms"
        )
        animation_panel = t.animation.panel if t.animation.enabled else "0.01ms"
        animation_content = t.animation.content if t.animation.enabled else "0.01ms"
        animation_dock = t.animation.dock if t.animation.enabled else "0.01ms"
        return {
            "--ule-color-background": t.colors.background,
            "--ule-color-background-alt": t.colors.background_alt,
            "--ule-color-surface": t.colors.surface,
            "--ule-color-surface-strong": t.colors.surface_strong,
            "--ule-color-text": t.colors.text,
            "--ule-color-muted": t.colors.muted,
            "--ule-color-accent": t.colors.accent,
            "--ule-color-accent-secondary": t.colors.accent_secondary,
            "--ule-color-border": t.colors.border,
            "--ule-color-border-accent": t.colors.border_accent,
            "--ule-color-focus": t.colors.focus,
            "--ule-color-gold": t.colors.gold,
            "--ule-color-gold-soft": t.colors.gold_soft,
            "--ule-color-success": t.colors.success,
            "--ule-color-warning": t.colors.warning,
            "--ule-color-error": t.colors.error,
            "--ule-font-body": t.typography.body,
            "--ule-font-display": t.typography.display,
            "--ule-font-monospace": t.typography.monospace,
            "--ule-font-base-size": t.typography.base_size,
            "--ule-font-heading-weight": t.typography.heading_weight,
            "--ule-icon-color": t.icons.color,
            "--ule-icon-accent": t.icons.accent,
            "--ule-icon-size": t.icons.size,
            "--ule-icon-family": t.icons.family,
            "--ule-card-background": t.surfaces.card_background,
            "--ule-card-border": t.surfaces.card_border,
            "--ule-card-radius": t.surfaces.card_radius,
            "--ule-card-shadow": t.surfaces.card_shadow,
            "--ule-card-hover-shadow": t.surfaces.card_hover_shadow,
            "--ule-glass-blur": t.surfaces.glass_blur,
            "--ule-dock-blur": t.surfaces.dock_blur,
            "--ule-scene-border": t.surfaces.scene_border,
            "--ule-scene-radius": t.surfaces.scene_radius,
            "--ule-home-dock-background": t.surfaces.home_dock_background,
            "--ule-home-dock-border": t.surfaces.home_dock_border,
            "--ule-home-dock-radius": t.surfaces.home_dock_radius,
            "--ule-world-dock-background": t.surfaces.world_dock_background,
            "--ule-world-dock-border": t.surfaces.world_dock_border,
            "--ule-world-dock-radius": t.surfaces.world_dock_radius,
            "--ule-world-dock-item-radius": t.surfaces.world_dock_item_radius,
            "--ule-button-background": t.buttons.background,
            "--ule-button-primary-background": t.buttons.primary_background,
            "--ule-button-text": t.buttons.text,
            "--ule-button-border": t.buttons.border,
            "--ule-button-radius": t.buttons.radius,
            "--ule-button-shadow": t.buttons.shadow,
            "--ule-button-hint-background": t.buttons.hint_background,
            "--ule-button-hint-border": t.buttons.hint_border,
            "--ule-button-hint-text": t.buttons.hint_text,
            "--ule-button-orbit-background": t.buttons.orbit_background,
            "--ule-button-orbit-border": t.buttons.orbit_border,
            "--ule-button-orbit-text": t.buttons.orbit_text,
            "--ule-layout-app-max-width": t.layout.app_max_width,
            "--ule-layout-scene-max-width": t.layout.scene_max_width,
            "--ule-layout-content-padding": t.layout.content_padding,
            "--ule-layout-home-dock-max-width": t.layout.home_dock_max_width,
            "--ule-layout-world-dock-max-width": t.layout.world_dock_max_width,
            "--ule-layout-gap": t.layout.gap,
            "--ule-widget-background": t.widgets.background,
            "--ule-widget-border": t.widgets.border,
            "--ule-widget-radius": t.widgets.radius,
            "--ule-widget-shadow": t.widgets.shadow,
            "--ule-input-background": t.widgets.input_background,
            "--ule-input-border": t.widgets.input_border,
            "--ule-dialog-background": t.widgets.dialog_background,
            "--ule-dashboard-background": t.widgets.dashboard_background,
            "--ule-metric-background": t.widgets.metric_background,
            "--ule-metric-border": t.widgets.metric_border,
            "--ule-tab-background": t.widgets.tab_background,
            "--ule-tab-border": t.widgets.tab_border,
            "--ule-animation-fast": animation_fast,
            "--ule-animation-normal": animation_normal,
            "--ule-animation-label": animation_label,
            "--ule-animation-slow": animation_slow,
            "--ule-animation-world-reveal": animation_world_reveal,
            "--ule-animation-panel": animation_panel,
            "--ule-animation-content": animation_content,
            "--ule-animation-dock": animation_dock,
            "--ule-animation-easing": t.animation.easing,
            "--ule-color-scheme": "light dark" if t.mode == "system" else t.mode,
            "--ule-background-world-map": t.backgrounds.world_map,
            "--ule-background-w01": t.backgrounds.w01,
            "--ule-background-w02": t.backgrounds.w02,
            "--ule-background-w03": t.backgrounds.w03,
            "--ule-background-w04": t.backgrounds.w04,
            "--ule-background-w05": t.backgrounds.w05,
            "--ule-background-w06": t.backgrounds.w06,
            "--ule-background-w07": t.backgrounds.w07,
            "--ule-background-w08": t.backgrounds.w08,
            "--ule-background-w09": t.backgrounds.w09,
        }

    def render_css(self, theme: ThemeContract) -> str:
        """Render a declaration-only override block from validated values."""

        theme_id = _safe_theme_id(theme.theme_id)
        safe_variables = {
            name: _safe_css_value(name, value)
            for name, value in self.css_variables(theme).items()
        }
        declarations = "\n".join(
            f"  {name}: {value};" for name, value in safe_variables.items()
        )
        return f':root[data-ule-theme="{theme_id}"], :root {{\n{declarations}\n}}'
