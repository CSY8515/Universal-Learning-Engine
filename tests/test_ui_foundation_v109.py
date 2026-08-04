"""Release v1.09 UI Foundation compatibility verification."""

from __future__ import annotations

from pathlib import Path
import unittest

import pytest

from ui.adapter import ThemeAdapter, ThemeContractError
from ui.contracts import UI_FOUNDATION_INTERFACE_VERSION
from ui.interface import UltraBrainUIInterface, get_ui_compatibility_layer
from ui.theme import apply_official_theme


ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "assets" / "ule.css").read_text(encoding="utf-8")


def test_public_compatibility_layer_implements_host_interface() -> None:
    layer = get_ui_compatibility_layer()
    assert isinstance(layer, UltraBrainUIInterface)
    assert layer.resolve_theme().interface_version == UI_FOUNDATION_INTERFACE_VERSION


def test_default_contract_preserves_official_visual_baseline() -> None:
    theme = ThemeAdapter().adapt()
    tokens = theme.tokens
    assert theme.theme_id == "ule-official"
    assert tokens.mode == "dark"
    assert tokens.colors.background == "#02060b"
    assert tokens.colors.accent == "#58a7ff"
    assert tokens.colors.gold == "#e1bd6b"
    assert tokens.typography.body.startswith('"Pretendard"')
    assert tokens.typography.display.startswith('"Batang"')
    assert tokens.surfaces.scene_radius == "1.5rem"
    assert tokens.layout.scene_max_width == "1600px"
    assert tokens.animation.world_reveal == "1.05s"


def test_adapter_accepts_every_required_ultra_brain_setting_group() -> None:
    settings = {
        "theme_id": "ultra-brain-custom",
        "interface_version": "1.0",
        "mode": "light",
        "colors": {"accent": "#123456", "background": "#ffffff"},
        "typography": {"body": "Inter, sans-serif"},
        "icons": {"family": "Symbols", "color": "#111111"},
        "surfaces": {"card_radius": "20px", "card_shadow": "none"},
        "buttons": {"radius": "8px", "background": "#eeeeee"},
        "layout": {"app_max_width": "1440px", "gap": "12px"},
        "widgets": {"background": "#f8f8f8", "radius": "10px"},
        "animation": {"enabled": False, "easing": "linear"},
        "backgrounds": {"w01": 'url("learning-light.png")'},
    }
    theme = ThemeAdapter().adapt(settings)
    css = ThemeAdapter().render_css(theme)
    assert theme.tokens.mode == "light"
    assert theme.tokens.colors.accent == "#123456"
    assert theme.tokens.typography.body == "Inter, sans-serif"
    assert theme.tokens.icons.family == "Symbols"
    assert theme.tokens.surfaces.card_radius == "20px"
    assert theme.tokens.buttons.radius == "8px"
    assert theme.tokens.layout.app_max_width == "1440px"
    assert theme.tokens.widgets.background == "#f8f8f8"
    assert theme.tokens.backgrounds.w01 == 'url("learning-light.png")'
    assert "--ule-animation-fast: 0.01ms" in css
    assert "--ule-color-scheme: light" in css


@pytest.mark.parametrize(
    "settings",
    [
        {"unknown": "value"},
        {"mode": "neon"},
        {"theme_id": 'bad\"] {}'},
        {"colors": {"unknown": "#fff"}},
        {"colors": {"accent": "red; background: black"}},
        {"backgrounds": {"w01": "url(javascript:alert(1))"}},
        {"animation": {"enabled": "yes"}},
        {"interface_version": "2.0"},
    ],
)
def test_adapter_rejects_unknown_or_unsafe_payloads(settings: dict) -> None:
    with pytest.raises(ThemeContractError):
        ThemeAdapter().adapt(settings)


def test_registry_covers_all_existing_ui_modules() -> None:
    modules = set(get_ui_compatibility_layer().ui_registry.module_ids())
    assert modules == {
        "Dashboard",
        "Learning",
        "CBT",
        "Recovery",
        "Challenge",
        "Analytics",
        "Reports",
        "AI",
        "Planner",
        "Library",
        "Management",
        "My Learning",
    }


def test_registry_covers_every_shared_component_family() -> None:
    components = set(get_ui_compatibility_layer().ui_registry.component_ids())
    assert components == {
        "background",
        "layout",
        "header",
        "navigation",
        "card",
        "button",
        "widget",
        "dialog",
        "icon",
        "typography",
        "animation",
    }


def test_all_adapter_variables_are_declared_and_consumed_by_repository_css() -> None:
    variables = ThemeAdapter.css_variables(ThemeAdapter().adapt())
    missing = [name for name in variables if name not in CSS]
    assert missing == []
    required_consumers = {
        "--ule-font-body",
        "--ule-icon-family",
        "--ule-card-background",
        "--ule-button-background",
        "--ule-layout-app-max-width",
        "--ule-widget-background",
        "--ule-animation-fast",
        "--ule-background-world-map",
        *(f"--ule-background-w0{index}" for index in range(1, 10)),
    }
    for variable in required_consumers:
        assert f"var({variable})" in CSS


def test_every_module_resolves_to_a_registered_background_contract() -> None:
    layer = get_ui_compatibility_layer()
    for module_id in layer.ui_registry.module_ids():
        contract = layer.module_contract(module_id)
        assert contract.background_token.startswith("backgrounds.")
        assert "background" in contract.components
        assert "widget" in contract.components
        assert "button" in contract.components


def test_theme_loader_keeps_static_css_and_appends_validated_overrides() -> None:
    calls: list[tuple[str, bool]] = []

    class FakeStreamlit:
        @staticmethod
        def markdown(value: str, unsafe_allow_html: bool = False) -> None:
            calls.append((value, unsafe_allow_html))

    apply_official_theme(
        FakeStreamlit,
        {"theme_id": "host-theme", "colors": {"accent": "#123456"}},
    )
    style = calls[0][0]
    assert style.startswith("<style>:root {")
    assert style.index("--ule-color-accent: #58a7ff") < style.rindex(
        "--ule-color-accent: #123456"
    )
    assert calls[0][1] is True


def test_theme_adapter_has_no_learner_or_runtime_state_dependency() -> None:
    source = (ROOT / "ui" / "adapter.py").read_text(encoding="utf-8")
    forbidden = ("session_state", "streamlit", "learner", "database", "api_key")
    assert all(term not in source.casefold() for term in forbidden)


class UICompatibilityAutomaticTest(unittest.TestCase):
    """Expose the complete v1.09 verification through unittest discovery."""

    def test_complete_ui_foundation_contract(self) -> None:
        test_public_compatibility_layer_implements_host_interface()
        test_default_contract_preserves_official_visual_baseline()
        test_adapter_accepts_every_required_ultra_brain_setting_group()
        for settings in (
            {"unknown": "value"},
            {"mode": "neon"},
            {"theme_id": 'bad\"] {}'},
            {"colors": {"unknown": "#fff"}},
            {"colors": {"accent": "red; background: black"}},
            {"backgrounds": {"w01": "url(javascript:alert(1))"}},
            {"animation": {"enabled": "yes"}},
            {"interface_version": "2.0"},
        ):
            with self.subTest(settings=settings):
                test_adapter_rejects_unknown_or_unsafe_payloads(settings)
        test_registry_covers_all_existing_ui_modules()
        test_registry_covers_every_shared_component_family()
        test_all_adapter_variables_are_declared_and_consumed_by_repository_css()
        test_every_module_resolves_to_a_registered_background_contract()
        test_theme_loader_keeps_static_css_and_appends_validated_overrides()
        test_theme_adapter_has_no_learner_or_runtime_state_dependency()
