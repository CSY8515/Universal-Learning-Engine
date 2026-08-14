"""Ultra Brain inherited world-theme propagation acceptance tests."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

from ui.adapter import ThemeAdapter
from ui.interface import get_ui_compatibility_layer
from ui.propagation import (
    ADJUSTMENT_RANGES,
    PROPAGATION_TARGETS,
    THEME_KEYS,
    resolve_inherited_theme,
)


ROOT = Path(__file__).resolve().parents[1]
WORLD_IDS = {
    "official": "sun-world",
    "light": "paper-daylight-world",
    "dark": "quiet-canopy-world",
    "calm": "calm-wetland-world",
    "universe": "indigo-orbit-world",
    "galaxy": "rose-nebula-world",
    "ecosystem": "living-canopy-world",
    "ocean": "deep-tide-world",
    "grassland": "sunlit-field-world",
    "lava": "molten-core-world",
    "minimal": "signal-world",
    "paper": "archive-paper-world",
    "archive": "bronze-record-world",
}


def inherited_query(theme: str) -> dict[str, str]:
    return {
        "source": "ultra-brain",
        "contract": "ultra-brain.ui/v1",
        "interface": "1.0",
        "target": "os-ecosystem",
        "scope": "global",
        "propagation": "automatic",
        "theme": theme,
        "world": WORLD_IDS[theme],
        "revision": "0.985",
        "uiLocks": json.dumps(
            {
                "position": False,
                "size": False,
                "background": False,
                "layout": False,
                "color": False,
                "texture": False,
                "lighting": False,
                "component": False,
                "layer": False,
            }
        ),
        "propagationTargets": json.dumps(PROPAGATION_TARGETS),
        "propagationLocks": "{}",
        "propagationOverrides": "{}",
    }


class InheritedThemePropagationTests(unittest.TestCase):
    def test_no_query_preserves_the_official_baseline(self) -> None:
        self.assertIsNone(resolve_inherited_theme({}))

    def test_official_defaults_preserve_baseline_but_adjustments_apply(self) -> None:
        baseline = resolve_inherited_theme(inherited_query("official"))
        assert baseline is not None
        self.assertIsNone(baseline.settings)
        self.assertEqual(baseline.effect_css, "")

        adjusted = inherited_query("official")
        adjusted.update({"brightness": "1.18", "contrast": "1.12", "texture": "1.2"})
        result = resolve_inherited_theme(adjusted)
        assert result is not None
        self.assertIsNone(result.settings)
        self.assertIn("--ule-inherited-brightness: 1.18", result.effect_css)
        self.assertIn("--ule-inherited-contrast: 1.12", result.effect_css)
        self.assertIn("radial-gradient(circle at 18% 27%", result.effect_css)

    def test_every_registered_world_theme_has_a_local_real_image(self) -> None:
        self.assertEqual(len(THEME_KEYS), 13)
        for theme in THEME_KEYS:
            with self.subTest(theme=theme):
                result = resolve_inherited_theme(inherited_query(theme))
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(result.theme, theme)
                if theme == "official":
                    self.assertIsNone(result.settings)
                    continue
                asset = ROOT / "static" / "themes" / f"{theme}.png"
                self.assertTrue(asset.is_file())
                header = asset.read_bytes()[:24]
                self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
                self.assertGreaterEqual(int.from_bytes(header[16:20], "big"), 1671)
                self.assertEqual(int.from_bytes(header[20:24], "big"), 941)

                settings = result.settings
                assert settings is not None
                expected = f'url("./app/static/themes/{theme}.png")'
                backgrounds = settings["backgrounds"]
                self.assertEqual(backgrounds["world_map"], expected)
                for index in range(1, 10):
                    self.assertEqual(backgrounds[f"w{index:02d}"], expected)
                self.assertIn("colors", settings)
                self.assertIn("widgets", settings)
                self.assertIn("buttons", settings)
                ThemeAdapter().adapt(settings)

    def test_every_functional_registry_entry_receives_the_theme_background(self) -> None:
        result = resolve_inherited_theme(inherited_query("ocean"))
        assert result is not None and result.settings is not None
        backgrounds = result.settings["backgrounds"]
        registry = get_ui_compatibility_layer().ui_registry
        for module_id in registry.module_ids():
            with self.subTest(module=module_id):
                token = registry.module(module_id).background_token.split(".", 1)[1]
                self.assertIn(token, backgrounds)
                self.assertEqual(
                    backgrounds[token],
                    'url("./app/static/themes/ocean.png")',
                )

    def test_ule_lock_keeps_local_theme_while_os_lock_does_not_leak(self) -> None:
        locked = inherited_query("lava")
        locked["propagationLocks"] = json.dumps(
            {"universal-learning-engine": list(PROPAGATION_TARGETS)}
        )
        result = resolve_inherited_theme(locked)
        assert result is not None
        self.assertIsNone(result.settings)
        self.assertEqual(result.blocked_targets, PROPAGATION_TARGETS)
        self.assertEqual(result.effect_css, "")

        os_only = inherited_query("lava")
        os_only["propagationLocks"] = json.dumps(
            {"os-ecosystem": ["theme", "background", "color"]}
        )
        result = resolve_inherited_theme(os_only)
        assert result is not None and result.settings is not None
        self.assertIn("backgrounds", result.settings)
        self.assertIn("colors", result.settings)

    def test_override_can_preserve_only_the_requested_category(self) -> None:
        query = inherited_query("grassland")
        query["propagationOverrides"] = json.dumps(
            {"universal-learning-engine": ["background"]}
        )
        result = resolve_inherited_theme(query)
        assert result is not None and result.settings is not None
        self.assertNotIn("backgrounds", result.settings)
        self.assertIn("colors", result.settings)
        self.assertIn("widgets", result.settings)

        color_locked = inherited_query("ocean")
        color_locked["propagationLocks"] = json.dumps(
            {"universal-learning-engine": ["color"]}
        )
        result = resolve_inherited_theme(color_locked)
        assert result is not None and result.settings is not None
        self.assertNotIn("colors", result.settings)
        self.assertIn("backgrounds", result.settings)
        self.assertNotIn("card_background", result.settings["surfaces"])
        self.assertNotIn("background", result.settings["widgets"])

    def test_legacy_override_is_scoped_to_ule_only(self) -> None:
        os_target = inherited_query("archive")
        os_target.update({"target": "os-ecosystem", "override": "1"})
        result = resolve_inherited_theme(os_target)
        assert result is not None and result.settings is not None

        ule_target = inherited_query("archive")
        ule_target.update({"target": "universal-learning-engine", "override": "1"})
        result = resolve_inherited_theme(ule_target)
        assert result is not None
        self.assertIsNone(result.settings)
        self.assertEqual(result.effect_css, "")

    def test_adjustments_are_clamped_and_rendered_as_closed_css_variables(self) -> None:
        query = inherited_query("calm")
        query.update(
            {
                "brightness": "99",
                "contrast": "bad",
                "saturation": "0",
                "hue": "-99",
                "lighting": "1.25",
                "shadow": "1.4",
                "glow": "1.7",
                "texture": "1.2",
                "blur": "4",
                "transparency": "0.7",
            }
        )
        result = resolve_inherited_theme(query)
        assert result is not None
        for declaration in (
            "--ule-inherited-brightness: 1.3",
            "--ule-inherited-contrast: 1",
            "--ule-inherited-saturation: 0.5",
            "--ule-inherited-hue: -30deg",
            "--ule-inherited-blur: 4px",
            "--ule-inherited-opacity: 0.7",
            "--ule-inherited-content-shadow: 0 25.2px 89.6px",
            "--ule-inherited-content-glow: 0 0 21px",
        ):
            self.assertIn(declaration, result.effect_css)
        self.assertIn("radial-gradient(circle at 18% 27%", result.effect_css)
        self.assertNotIn("repeating-linear-gradient", result.effect_css)
        for key, (minimum, maximum, _default) in ADJUSTMENT_RANGES.items():
            self.assertLessEqual(minimum, maximum, key)

    def test_unknown_and_malformed_values_fall_back_safely(self) -> None:
        malformed = inherited_query("ocean")
        malformed.update(
            {
                "theme": "../../bad",
                "world": "<script>",
                "revision": "bad revision",
                "propagationTargets": "not-json",
                "propagationLocks": "{bad",
            }
        )
        self.assertIsNone(resolve_inherited_theme(malformed))

    def test_contract_identity_scope_target_and_world_are_fail_closed(self) -> None:
        invalid_values = {
            "source": "someone-else",
            "contract": "ultra-brain.ui/v2",
            "interface": "2.0",
            "target": "unknown-node",
            "scope": "os-ecosystem",
            "propagation": "unknown",
            "world": "ocean-world",
            "revision": "bad revision",
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field):
                query = inherited_query("ocean")
                query[field] = value
                self.assertIsNone(resolve_inherited_theme(query))

        for field in ("source", "contract", "interface", "target", "scope", "propagation"):
            with self.subTest(missing=field):
                query = inherited_query("ocean")
                query.pop(field)
                self.assertIsNone(resolve_inherited_theme(query))

    def test_forwarded_os_target_is_accepted_for_ule(self) -> None:
        result = resolve_inherited_theme(inherited_query("ocean"))
        assert result is not None
        self.assertEqual(result.theme, "ocean")
        self.assertEqual(result.world, "deep-tide-world")
        self.assertEqual(result.revision, "0.985")

    def test_present_contract_json_must_be_valid(self) -> None:
        for field, value in (
            ("propagationTargets", "not-json"),
            ("propagationTargets", "{}"),
            ("propagationLocks", "[]"),
            ("propagationLocks", "{bad"),
            ("propagationOverrides", "[]"),
            ("propagationOverrides", "{bad"),
            ("uiLocks", "[]"),
            ("uiLocks", "{bad"),
            ("uiLocks", json.dumps({"unknown": True})),
            ("uiLocks", json.dumps({"layout": "yes"})),
        ):
            with self.subTest(field=field, value=value):
                query = inherited_query("ocean")
                query[field] = value
                self.assertIsNone(resolve_inherited_theme(query))

    def test_ui_locks_map_to_downstream_categories(self) -> None:
        expected = {
            "position": {"componentPosition"},
            "size": {"componentSize"},
            "background": {"background"},
            "layout": {"layout"},
            "color": {"color"},
            "texture": {"texture"},
            "lighting": {"lighting"},
            "component": {"componentPosition", "componentSize", "visibility"},
            "layer": {"visibility"},
        }
        for lock, targets in expected.items():
            with self.subTest(lock=lock):
                query = inherited_query("ocean")
                ui_locks = {key: False for key in expected}
                ui_locks[lock] = True
                query["uiLocks"] = json.dumps(ui_locks)
                result = resolve_inherited_theme(query)
                assert result is not None
                self.assertTrue(targets.issubset(set(result.blocked_targets)))

        background_locked = inherited_query("ocean")
        background_locked["uiLocks"] = json.dumps(
            {
                "position": False,
                "size": False,
                "background": True,
                "layout": False,
                "color": False,
                "texture": False,
                "lighting": False,
                "component": False,
                "layer": False,
            }
        )
        result = resolve_inherited_theme(background_locked)
        assert result is not None and result.settings is not None
        self.assertNotIn("backgrounds", result.settings)
        self.assertIn("colors", result.settings)

    def test_selective_targets_do_not_expand_from_theme(self) -> None:
        background_only = inherited_query("ocean")
        background_only["propagationTargets"] = json.dumps(["background"])
        result = resolve_inherited_theme(background_only)
        assert result is not None and result.settings is not None
        self.assertEqual(set(result.settings), {"theme_id", "interface_version", "backgrounds"})
        self.assertEqual(result.effect_css, "")

        theme_only = inherited_query("ocean")
        theme_only["propagationTargets"] = json.dumps(["theme"])
        result = resolve_inherited_theme(theme_only)
        assert result is not None and result.settings is not None
        self.assertNotIn("backgrounds", result.settings)
        self.assertNotIn("colors", result.settings)
        self.assertEqual(set(result.settings["surfaces"]), {
            "card_radius",
            "scene_radius",
            "home_dock_radius",
            "world_dock_radius",
            "world_dock_item_radius",
        })

    def test_full_override_is_as_neutral_as_full_lock(self) -> None:
        query = inherited_query("lava")
        query["propagationOverrides"] = json.dumps(
            {"universal-learning-engine": list(PROPAGATION_TARGETS)}
        )
        result = resolve_inherited_theme(query)
        assert result is not None
        self.assertIsNone(result.settings)
        self.assertEqual(result.effect_css, "")

    def test_layout_is_clamped_and_respects_category_locks(self) -> None:
        layout = {
            "topbar": {"x": 999, "y": -999, "scale": 9, "visible": False},
            "center": {"x": 18, "y": 24, "scale": 0.8, "visible": True},
            "seed": {"x": -22, "y": 12, "scale": 1.1, "visible": False},
            "rail": {"x": 4, "y": 5, "scale": 1.2, "visible": True},
        }
        query = inherited_query("ocean")
        query["layout"] = json.dumps(layout)
        result = resolve_inherited_theme(query)
        assert result is not None
        self.assertIn(
            "--ule-inherited-topbar-transform: translate(80px, -60px) scale(1.32)",
            result.effect_css,
        )
        self.assertIn("--ule-inherited-topbar-display: none", result.effect_css)
        self.assertIn("--ule-inherited-seed-display: none", result.effect_css)

        locked = dict(query)
        locked["propagationLocks"] = json.dumps(
            {
                "universal-learning-engine": [
                    "componentPosition",
                    "componentSize",
                    "visibility",
                ]
            }
        )
        result = resolve_inherited_theme(locked)
        assert result is not None
        self.assertNotIn("--ule-inherited-topbar-transform", result.effect_css)
        self.assertNotIn("--ule-inherited-topbar-display", result.effect_css)

        malformed = inherited_query("ocean")
        malformed["layout"] = "[]"
        self.assertIsNone(resolve_inherited_theme(malformed))

    def test_layout_density_is_separate_from_component_coordinates(self) -> None:
        query = inherited_query("ocean")
        query["density"] = "compact"
        result = resolve_inherited_theme(query)
        assert result is not None and result.settings is not None
        self.assertEqual(result.settings["layout"]["gap"], ".75rem")

        query["propagationLocks"] = json.dumps(
            {"universal-learning-engine": ["layout"]}
        )
        result = resolve_inherited_theme(query)
        assert result is not None and result.settings is not None
        self.assertNotIn("layout", result.settings)

    def test_v1096_original_ui_is_isolated_from_inherited_effects(self) -> None:
        css = (ROOT / "assets" / "ule.css").read_text(encoding="utf-8")
        propagation_source = (ROOT / "ui" / "propagation.py").read_text(
            encoding="utf-8"
        )
        match = re.search(
            r"@keyframes ule-world-reveal\s*\{(?P<body>.*?)\n\}",
            css,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        body = match.group("body") if match else ""
        self.assertIn("filter:", body)
        self.assertIn("opacity:", body)
        self.assertNotIn("repeating-linear-gradient", propagation_source)

        for inherited in (
            "--ule-inherited-brightness",
            "--ule-inherited-contrast",
            "--ule-inherited-saturation",
            "--ule-inherited-hue",
            "--ule-inherited-blur",
            "--ule-inherited-opacity",
            "--ule-inherited-center-display",
            "--ule-inherited-seed-display",
            "--ule-inherited-rail-display",
        ):
            self.assertNotIn(inherited, css)

        for index in range(1, 10):
            self.assertIn(f".ule-world-backdrop--w{index:02d}", css)


if __name__ == "__main__":
    unittest.main()
