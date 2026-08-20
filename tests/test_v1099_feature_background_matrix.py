from __future__ import annotations

from pathlib import Path

from ui.theme import (
    FEATURE_WORLD_DEFINITIONS,
    query_contract_from_mapping,
    resolve_feature_background,
    resolve_theme_world,
)


ROOT = Path(__file__).resolve().parents[1]
DARK_ASSETS = {
    "Learning": "theme-role-assets/dark/learning-background.png",
    "Recovery": "theme-role-assets/dark/recovery-background.png",
    "Challenge": "theme-role-assets/dark/challenge-background.png",
    "Analytics": "theme-role-assets/dark/analytics-background.png",
    "AI": "theme-role-assets/dark/ai-background.png",
    "Planner": "theme-role-assets/dark/learning-plan-background.png",
    "Library": "theme-role-assets/dark/library-background.png",
    "Management": "theme-role-assets/dark/management-background.png",
    "My Learning": "theme-role-assets/dark/my-learning-background.png",
}


def query(**extra: object) -> dict[str, object]:
    return {
        "source": "ultra-brain",
        "contract": "ultra-brain.ui/v1",
        "interface": "1.0",
        "theme": "dark",
        "world": "quiet-canopy-world",
        "revision": "2",
        "target": "universal-learning-engine",
        "asset_registry": "ui-theme-registry",
        "asset_registry_version": "1.0.0",
        "project_id": "universal-learning-engine",
        "visual_role": "HOME_BACKGROUND",
        "asset_revision": "2",
        **extra,
    }


def test_complete_dark_feature_background_matrix_is_deterministic_and_safe() -> None:
    world = resolve_theme_world(query_contract_from_mapping(query()))
    assert world.visual_theme_id == "dark"
    assert world.theme_asset_required is False

    first_pass: dict[str, tuple[str, str, str]] = {}
    for view, definition in FEATURE_WORLD_DEFINITIONS.items():
        resolved = resolve_feature_background(world, view)
        first_pass[view] = resolved
        asset, source, fallback = resolved
        expected = DARK_ASSETS[view]
        assert asset == expected
        assert (ROOT / "static" / asset).is_file()
        assert source == "theme-project-feature-role"
        assert fallback == "NONE"

    # A -> B -> A must never leak the second Feature's asset into the first.
    assert resolve_feature_background(world, "Planner") == first_pass["Planner"]
    assert resolve_feature_background(world, "Learning") == first_pass["Learning"]
    assert resolve_feature_background(world, "Planner") == first_pass["Planner"]


def test_feature_role_context_activates_only_an_approved_dark_package() -> None:
    for view in FEATURE_WORLD_DEFINITIONS:
        feature_id = view.lower().replace(" ", "-")
        contract = query_contract_from_mapping(
            query(visual_role="FEATURE_BACKGROUND", feature_id=feature_id)
        )
        world = resolve_theme_world(contract)
        assert world.visual_theme_id == "dark"
        assert world.theme_asset_required is False
        assert resolve_feature_background(world, view)[0] == DARK_ASSETS[view]

    missing = resolve_theme_world(
        query_contract_from_mapping(
            query(visual_role="FEATURE_BACKGROUND", feature_id="unregistered")
        )
    )
    assert missing.visual_theme_id == "official"
    assert missing.theme_asset_required is True


def test_official_return_and_dark_reentry_preserve_feature_identity() -> None:
    dark = resolve_theme_world(query_contract_from_mapping(query()))
    official = resolve_theme_world(
        query_contract_from_mapping(
            query(theme="official", world="sun-world", visual_role="HOME_BACKGROUND")
        )
    )
    dark_again = resolve_theme_world(query_contract_from_mapping(query()))

    for view, definition in FEATURE_WORLD_DEFINITIONS.items():
        official_asset, source, fallback = resolve_feature_background(official, view)
        assert official_asset == f"worlds/{definition.slug}.png"
        assert source == "official"
        assert fallback == "NONE"
        assert resolve_feature_background(dark_again, view) == resolve_feature_background(
            dark, view
        )
