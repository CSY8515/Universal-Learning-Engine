"""v1.098 dedicated feature-background regression tests."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _block(source: str, selector: str) -> str:
    start = source.index(selector)
    return source[start : source.index("\n}", start)]


def test_repository_feature_background_is_full_color() -> None:
    styles = (ROOT / "assets" / "ule.css").read_text(encoding="utf-8")
    feature_art = _block(styles, ".ule-world-backdrop::before {")

    assert "background-image: var(--ule-feature-image)" in feature_art
    assert "opacity: 1" in feature_art
    assert "mix-blend-mode: normal" in feature_art
    assert "filter: none" in feature_art


def test_runtime_lock_wins_over_stale_deployment_css() -> None:
    application = (ROOT / "app.py").read_text(encoding="utf-8")

    assert 'data-ule-feature-background-lock="v1.098"' in application
    assert "opacity: 1 !important" in application
    assert "mix-blend-mode: normal !important" in application
    assert "filter: none !important" in application
    assert application.index("apply_official_theme(st") < application.index(
        "st.markdown(FEATURE_BACKGROUND_LOCK_CSS"
    )


def test_official_styles_are_not_cached_across_deployments() -> None:
    theme_source = (ROOT / "ui" / "theme.py").read_text(encoding="utf-8")
    official_styles = theme_source.index("def _official_styles()")
    preceding_source = theme_source[max(0, official_styles - 120) : official_styles]

    assert "@lru_cache" not in preceding_source
