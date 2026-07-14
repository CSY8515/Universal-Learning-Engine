import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class V10UIContractTests(unittest.TestCase):
    def test_official_theme_is_dark_and_original(self):
        config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
        css = (ROOT / "assets" / "ule.css").read_text(encoding="utf-8")
        combined = (config + css).casefold()
        self.assertIn('base = "dark"', config)
        self.assertIn("#06101a", combined)
        self.assertIn("#35c8dd", combined)
        self.assertNotIn("jarvis", combined)
        self.assertNotIn("iron man", combined)

    def test_theme_loader_accepts_only_static_repository_css(self):
        source = (ROOT / "ui" / "theme.py").read_text(encoding="utf-8")
        self.assertIn("_STYLE_PATH.read_text", source)
        self.assertNotIn("session_state", source)
        self.assertNotIn("OPENAI_API_KEY", source)

    def test_responsive_and_reduced_motion_rules_exist(self):
        css = (ROOT / "assets" / "ule.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 700px)", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn(":focus-visible", css)


if __name__ == "__main__":
    unittest.main()
