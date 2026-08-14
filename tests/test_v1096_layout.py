"""v1.096 AI connection and subject-management layout regression tests."""

from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

from tests._streamlit_case import IsolatedWorldStateTestCase


ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "assets" / "ule.css"


class V1096LayoutTests(IsolatedWorldStateTestCase):
    def test_management_reuses_the_common_split_feature_layout(self) -> None:
        styles = STYLE_PATH.read_text(encoding="utf-8")

        content_start = styles.index('[class*="st-key-ule_world_content_"] {')
        content_block = styles[content_start : styles.index("\n}", content_start)]
        self.assertIn("width: min(790px, calc(100% - 1rem))", content_block)
        self.assertIn("margin: 1.4rem 0 4rem", content_block)

        self.assertIn(
            ".ule-world-backdrop--w08 { --ule-feature-image: var(--ule-background-w08);",
            styles,
        )
        self.assertIn(".ule-world-backdrop::before {", styles)
        self.assertIn("background-image: var(--ule-feature-image)", styles)
        navigation_section = styles.index(
            "/* Compact navigation remains available in every World. */"
        )
        dock_start = styles.index(".st-key-ule_world_dock {", navigation_section)
        dock_block = styles[dock_start : styles.index("\n}", dock_start)]
        self.assertIn("position: fixed", dock_block)
        self.assertIn("bottom: 1rem", dock_block)
        self.assertNotIn("width: 100vw", content_block)

    def test_ai_connection_and_subject_controls_are_preserved(self) -> None:
        application = AppTest.from_file("app.py").run(timeout=20)
        self.assertFalse(application.exception)

        navigation = next(
            item for item in application.radio if item.label == "주요 메뉴"
        )
        navigation.set_value("Management").run(timeout=20)
        self.assertFalse(application.exception)

        headings = [item.value for item in application.subheader]
        self.assertIn("인공지능 연결", headings)
        self.assertIn("과목 관리", headings)

        inputs = [item.label for item in application.text_input]
        self.assertIn("인공지능 연결 키", inputs)
        self.assertIn("과목 추가", inputs)

        buttons = [item.label for item in application.button]
        self.assertIn("연결 키 등록", buttons)
        self.assertIn("연결 확인", buttons)
        self.assertIn("연결 키 삭제", buttons)
        self.assertIn("과목 저장", buttons)

        checkboxes = [item.label for item in application.checkbox]
        self.assertIn("연결 키 삭제에 동의합니다.", checkboxes)


if __name__ == "__main__":
    unittest.main()
