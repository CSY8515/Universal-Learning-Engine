from __future__ import annotations

from ui.theme import (
    query_contract_from_mapping,
    resolve_role_asset_reference,
    resolve_theme_world,
)


def query(**extra: object) -> dict[str, object]:
    return {
        "source": "ultra-brain",
        "contract": "ultra-brain.ui/v1",
        "interface": "1.0",
        "theme": "dark",
        "world": "quiet-canopy-world",
        "revision": "2",
        "target": "universal-learning-engine",
        **extra,
    }


def test_ule_accepts_registered_dark_home_package() -> None:
    values = query(
        asset_registry="ui-theme-registry",
        asset_registry_version="1.0.0",
        project_id="universal-learning-engine",
        visual_role="HOME_BACKGROUND",
        asset_revision="2",
    )
    contract = query_contract_from_mapping(values)
    assert contract["project_id"] == "universal-learning-engine"
    assert contract["visual_role"] == "HOME_BACKGROUND"
    asset, source, fallback = resolve_role_asset_reference(contract, "HOME_BACKGROUND")
    assert asset == "theme-role-assets/dark/home-background.png"
    assert source == "theme-project-role"
    assert fallback == "NONE"
    world = resolve_theme_world(contract)
    assert world.visual_theme_id == "dark"
    assert world.asset_state == "theme-project-role"
    assert world.theme_asset_required is False
    assert world.central_asset == "theme-role-assets/dark/central-world.png"
    assert world.navigation_skin_asset == "theme-role-assets/dark/navigation-object-skin.png"


def test_ule_home_context_is_not_reused_as_learning_plan_feature() -> None:
    contract = query_contract_from_mapping(
        query(
            asset_registry="ui-theme-registry",
            asset_registry_version="1.0.0",
            project_id="universal-learning-engine",
            visual_role="HOME_BACKGROUND",
            asset_revision="2",
        )
    )
    asset, source, fallback = resolve_role_asset_reference(
        contract, "FEATURE_BACKGROUND", "planner"
    )
    assert asset is None
    assert source == "missing-role-asset"
    assert fallback == "ASSET REQUIRED"


def test_ule_registered_feature_assets_resolve_independently() -> None:
    for feature_id, expected in (
        ("planner", "theme-role-assets/dark/learning-plan-background.png"),
        ("analytics", "theme-role-assets/dark/analytics-background.png"),
        ("learning", "theme-role-assets/dark/learning-background.png"),
        ("recovery", "theme-role-assets/dark/recovery-background.png"),
        ("challenge", "theme-role-assets/dark/challenge-background.png"),
        ("ai", "theme-role-assets/dark/ai-background.png"),
        ("library", "theme-role-assets/dark/library-background.png"),
        ("management", "theme-role-assets/dark/management-background.png"),
        ("my-learning", "theme-role-assets/dark/my-learning-background.png"),
    ):
        contract = query_contract_from_mapping(
            query(
                asset_registry="ui-theme-registry",
                asset_registry_version="1.0.0",
                project_id="universal-learning-engine",
                feature_id=feature_id,
                visual_role="FEATURE_BACKGROUND",
                asset_revision="2",
            )
        )
        asset, source, fallback = resolve_role_asset_reference(
            contract, "FEATURE_BACKGROUND", feature_id
        )
        assert asset == expected
        assert source == "theme-project-feature-role"
        assert fallback == "NONE"


def test_official_home_remains_the_safe_default() -> None:
    official = query_contract_from_mapping({**query(), "theme": "official"})
    asset, source, fallback = resolve_role_asset_reference(
        official, "HOME_BACKGROUND"
    )
    assert asset == "theme-official.png"
    assert source == "official-default"
    assert fallback == "NONE"
