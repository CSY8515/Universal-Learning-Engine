from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from tests._streamlit_case import IsolatedWorldStateTestCase
from ui import HOME_VIEW, NAVIGATION_OPTIONS
from ui.theme import WORLD_PRESENTATION


ROOT = Path(__file__).resolve().parent.parent
STYLE_PATH = ROOT / "assets" / "ule.css"
NAVIGATION_PATH = ROOT / "ui" / "navigation.py"
WORLD_ASSET_PATH = ROOT / "static" / "worlds"


class OfficialUiV107Tests(IsolatedWorldStateTestCase):
    def setUp(self):
        super().setUp()
        self.app = AppTest.from_file("app.py", default_timeout=6).run()
        self.assertFalse(self.app.exception)

    def navigation(self):
        return [item for item in self.app.radio if item.label == "주요 메뉴"][0]

    def test_world_map_is_the_presentation_home_without_domain_world_changes(self):
        self.assertEqual(self.app.session_state["active_view"], HOME_VIEW)
        self.assertEqual(len(NAVIGATION_OPTIONS), 10)
        self.assertEqual(
            NAVIGATION_OPTIONS[1:],
            (
                "Learning",
                "Recovery",
                "Challenge",
                "Analytics",
                "AI",
                "Planner",
                "Library",
                "Management",
                "My Learning",
            ),
        )

    def test_home_quick_dock_routes_to_existing_worlds(self):
        dock = [
            item
            for item in self.app.radio
            if item.label == "학습 세계 빠른 이동"
        ][0]
        dock.set_value("Planner").run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state["active_view"], "Planner")

    def test_all_nine_worlds_keep_their_functional_entry_points(self):
        expected_headers = (
            ("Learning", "학습"),
            ("Recovery", "회복 학습"),
            ("Challenge", "도전 학습"),
            ("Analytics", "학습 분석"),
            ("AI", "인공지능"),
            ("Planner", "학습 계획"),
            ("Library", "학습 자료실"),
            ("Management", "관리"),
            ("My Learning", "나의 학습"),
        )
        for world, heading in expected_headers:
            self.navigation().set_value(world).run()
            self.assertFalse(self.app.exception)
            self.assertIn(heading, [item.value for item in self.app.header])

    def test_each_world_has_a_dedicated_static_background(self):
        self.assertEqual(len(WORLD_PRESENTATION), 9)
        asset_names = {"world-map.png"}
        asset_names.update(
            f"{slug}.png"
            for slug, _label, _description, _place in WORLD_PRESENTATION.values()
        )
        self.assertEqual(
            asset_names,
            {path.name for path in WORLD_ASSET_PATH.glob("*.png")},
        )
        for asset_name in asset_names:
            asset = WORLD_ASSET_PATH / asset_name
            self.assertGreater(asset.stat().st_size, 100_000)

    def test_official_motion_and_accessibility_contract_is_static(self):
        styles = STYLE_PATH.read_text(encoding="utf-8")
        self.assertIn("--ule-world-crown-y", styles)
        self.assertIn("ule-world-reveal", styles)
        self.assertIn("label:hover", styles)
        self.assertIn("focus-visible", styles)
        self.assertIn("prefers-reduced-motion", styles)
        self.assertIn("backdrop-filter", styles)

    def test_home_copy_keeps_only_the_compact_engine_title(self):
        navigation = NAVIGATION_PATH.read_text(encoding="utf-8")
        self.assertIn("<h1>Universal Learning Engine</h1>", navigation)
        self.assertNotIn("하나로 이어지는 학습 생태계", navigation)
        self.assertNotIn("아홉 개의 학습 세계", navigation)


if __name__ == "__main__":
    unittest.main()
