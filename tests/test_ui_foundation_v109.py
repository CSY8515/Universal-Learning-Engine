"""v1.09 foundation and v1.091 Theme World integration verification."""

from __future__ import annotations

from pathlib import Path
import unittest

from ui.adapter import ThemeAdapter, ThemeContractError
from ui.contracts import UI_FOUNDATION_INTERFACE_VERSION
from ui.interface import UltraBrainUIInterface, get_ui_compatibility_layer
from ui.theme import (
    FEATURE_WORLD_DEFINITIONS,
    THEME_WORLD_DEFINITIONS,
    WORLD_PRESENTATION,
    apply_official_theme,
    query_adjustment_css,
    query_contract_from_mapping,
    resolve_applied_query_contract,
    resolve_theme_world,
    render_world_stage,
    theme_settings_from_mapping,
)


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


UNSAFE_SETTINGS = (
    {"unknown": "value"},
    {"mode": "neon"},
    {"theme_id": 'bad\"] {}'},
    {"colors": {"unknown": "#fff"}},
    {"colors": {"accent": "red; background: black"}},
    {"backgrounds": {"w01": "url(javascript:alert(1))"}},
    {"animation": {"enabled": "yes"}},
    {"interface_version": "2.0"},
)


def test_adapter_rejects_unknown_or_unsafe_payloads() -> None:
    for settings in UNSAFE_SETTINGS:
        try:
            ThemeAdapter().adapt(settings)
        except ThemeContractError:
            continue
        raise AssertionError(f"unsafe settings were accepted: {settings!r}")


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


def test_ultra_brain_theme_bridge_is_bounded_and_uses_existing_ule_worlds() -> None:
    payload = {
        "source": "ultra-brain",
        "contract": "ultra-brain.ui/v1",
        "interface": "1.0",
        "theme": "ocean",
        "world": "deep-tide-world",
        "revision": "3",
        "target": "universal-learning-engine",
        "propagation": "applied",
        "locks": "theme,background,unsafe",
        "override": "true",
        "locked_systems": "living-os,os_ecosystem,unknown",
        "overridden_systems": "universal_learning_engine",
        "brightness": "9",
        "contrast": "0.1",
        "saturation": "1.2",
        "hue": "bad",
        "lighting": "1.1",
        "shadow": "1.2",
        "glow": "1.3",
        "texture": "1.4",
        "blur": "2",
        "transparency": ".8",
        "ignore": "javascript:alert(1)",
    }
    contract = query_contract_from_mapping(payload)
    assert contract["world"] == "deep-tide-world"
    assert contract["revision"] == 3
    assert contract["interface"] == "1.0"
    assert contract["target"] == "universal-learning-engine"
    assert contract["propagation"] == "applied"
    assert contract["locks"] == ("theme", "background")
    assert contract["override"] is True
    assert contract["locked_systems"] == ("living-os", "os-ecosystem")
    assert contract["overridden_systems"] == ("universal-learning-engine",)
    assert contract["brightness"] == 1.3
    assert contract["contrast"] == 0.7
    assert "hue" not in contract
    assert all(name in contract for name in ("lighting", "shadow", "glow", "texture", "blur", "transparency"))

    settings = theme_settings_from_mapping(payload)
    assert settings["theme_id"] == "ocean"
    assert settings["colors"]["accent"] == "#56b8cf"
    assert theme_settings_from_mapping({"source": "other", "theme": "ocean"}) == {}
    assert theme_settings_from_mapping({"source": "ultra-brain", "theme": "not-approved"}) == {}

    css = query_adjustment_css(payload)
    assert 'data-ultra-brain-adjustments="v1"' in css
    assert "brightness(1.300)" in css
    assert "contrast(0.700)" in css
    assert "javascript" not in css


def test_theme_home_and_functional_worlds_use_real_distinct_assets() -> None:
    styles = (ROOT / "assets" / "ule.css").read_text(encoding="utf-8")
    assert (ROOT / "static" / "worlds" / "world-map.png").is_file()
    for theme_id, definition in THEME_WORLD_DEFINITIONS.items():
        asset = definition[0]
        assert (ROOT / "static" / "theme-worlds" / asset).is_file()
        assert f"--ule-background-theme-{theme_id}" in styles
        assert f'.ule-world-theme--{theme_id} {{ --ule-active-theme-image:' in styles
    for index in range(1, 10):
        slug = f"w{index:02d}"
        assert f".ule-world-backdrop--{slug} {{ --ule-feature-image: var(--ule-background-{slug});" in styles
        assert (ROOT / "static" / "worlds" / f"{slug}.png").is_file()
    assert WORLD_PRESENTATION["Learning"][0] == "w01"
    assert WORLD_PRESENTATION["Recovery"][0] == "w02"
    assert "background-image: var(--ule-active-theme-image)" in styles
    assert "--ule-home-detail-image: var(--ule-background-world-map)" in styles
    assert (
        '.st-key-ule_world_map_navigation:has(.ule-theme-context:not([data-theme-world="official"]))'
        in styles
    )
    assert "--ule-home-detail-image: linear-gradient(transparent, transparent)" in styles
    home_detail_start = styles.index(".st-key-ule_world_map_navigation::before")
    home_detail_block = styles[
        home_detail_start : styles.index("\n}", home_detail_start)
    ]
    assert "var(--ule-home-detail-image) center / cover no-repeat" in home_detail_block
    assert "var(--ule-background-world-map) center / cover no-repeat" not in home_detail_block
    assert "background-image: var(--ule-feature-image)" in styles
    assert "mix-blend-mode: luminosity" in styles


def test_theme_world_definition_preserves_source_world_and_revision() -> None:
    galaxy = resolve_theme_world(
        {
            "source": "ultra-brain",
            "theme": "galaxy",
            "world": "rose-nebula-world",
            "revision": "7",
        }
    )
    ocean = resolve_theme_world(
        {
            "source": "ultra-brain",
            "theme": "ocean",
            "world": "deep-tide-world",
            "revision": "8",
        }
    )
    assert galaxy.theme_id == "galaxy"
    assert galaxy.source_world_id == "rose-nebula-world"
    assert galaxy.revision == 7
    assert galaxy.home_asset != ocean.home_asset
    assert galaxy.metaphor != ocean.metaphor


def test_representative_features_render_distinct_scenes_in_the_same_theme() -> None:
    calls: list[str] = []

    class FakeStreamlit:
        @staticmethod
        def markdown(value: str, unsafe_allow_html: bool = False) -> None:
            assert unsafe_allow_html is True
            calls.append(value)

    theme_world = resolve_theme_world(
        {
            "source": "ultra-brain",
            "theme": "ocean",
            "world": "deep-tide-world",
            "revision": "4",
        }
    )
    slugs = [
        render_world_stage(FakeStreamlit, feature, theme_world)
        for feature in ("Learning", "Recovery", "Analytics")
    ]
    assert slugs == ["w01", "w02", "w04"]
    assert len(set(slugs)) == 3
    assert all('data-theme-world="ocean"' in markup for markup in calls)
    assert all('data-theme-source-world="deep-tide-world"' in markup for markup in calls)
    assert all('data-theme-revision="4"' in markup for markup in calls)
    for feature, markup in zip(("Learning", "Recovery", "Analytics"), calls):
        definition = FEATURE_WORLD_DEFINITIONS[feature]
        assert f'ule-world-backdrop--{definition.slug}' in markup
        assert f'data-feature-world="{definition.slug}"' in markup
        assert definition.motif in markup


def test_ule_lock_or_override_keeps_previous_applied_presentation() -> None:
    previous, remember_previous = resolve_applied_query_contract(
        {
            "source": "ultra-brain",
            "theme": "ocean",
            "world": "deep-tide-world",
            "revision": "3",
            "brightness": "1.2",
            "lighting": "1.1",
        }
    )
    assert remember_previous is True

    locked, remember_locked = resolve_applied_query_contract(
        {
            "source": "ultra-brain",
            "theme": "galaxy",
            "world": "rose-nebula-world",
            "revision": "4",
            "brightness": ".7",
            "lighting": ".2",
            "locked_systems": "universal_learning_engine",
        },
        previous,
    )
    assert remember_locked is False
    assert locked["theme"] == "ocean"
    assert locked["world"] == "deep-tide-world"
    assert locked["revision"] == 3
    assert locked["brightness"] == 1.2
    assert locked["lighting"] == 1.1
    assert locked["locked_systems"] == ("universal-learning-engine",)

    overridden, remember_overridden = resolve_applied_query_contract(
        {
            "source": "ultra-brain",
            "theme": "lava",
            "brightness": ".8",
            "overridden_systems": "universal-learning-engine",
        },
        previous,
    )
    assert remember_overridden is False
    assert overridden["theme"] == "ocean"
    assert overridden["brightness"] == 1.2

    fail_closed, remember_fail_closed = resolve_applied_query_contract(
        {
            "source": "ultra-brain",
            "theme": "universe",
            "brightness": "1.3",
            "locked_systems": "universal-learning-engine",
        }
    )
    assert remember_fail_closed is False
    assert fail_closed["theme"] == "official"
    assert "brightness" not in fail_closed

    other_system, remember_other = resolve_applied_query_contract(
        {
            "source": "ultra-brain",
            "theme": "calm",
            "locked_systems": "living-os",
        },
        previous,
    )
    assert remember_other is True
    assert other_system["theme"] == "calm"


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
        with self.subTest(case="unsafe and unknown payloads"):
            test_adapter_rejects_unknown_or_unsafe_payloads()
        test_registry_covers_all_existing_ui_modules()
        test_registry_covers_every_shared_component_family()
        test_all_adapter_variables_are_declared_and_consumed_by_repository_css()
        test_every_module_resolves_to_a_registered_background_contract()
        test_theme_loader_keeps_static_css_and_appends_validated_overrides()
        test_theme_home_and_functional_worlds_use_real_distinct_assets()
        test_theme_world_definition_preserves_source_world_and_revision()
        test_representative_features_render_distinct_scenes_in_the_same_theme()
        test_ule_lock_or_override_keeps_previous_applied_presentation()
        test_theme_adapter_has_no_learner_or_runtime_state_dependency()
