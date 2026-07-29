"""Trusted static theme loading for the official ULE interface."""

from functools import lru_cache
from pathlib import Path


_STYLE_PATH = Path(__file__).resolve().parent.parent / "assets" / "ule.css"


@lru_cache(maxsize=1)
def _official_styles() -> str:
    """Read repository-owned CSS once per process.

    The returned stylesheet is static source-controlled content. Learner topics,
    generated lessons, answers, secrets, and Pack data are never interpolated.
    """

    return _STYLE_PATH.read_text(encoding="utf-8")


def apply_official_theme(st_module) -> None:
    """Apply the official ULE skin without mixing user content into HTML."""

    st_module.markdown(f"<style>{_official_styles()}</style>", unsafe_allow_html=True)
    st_module.markdown(
        """
        <div class="ule-brand" aria-label="통합 학습 엔진">
          <div class="ule-brand__mark">학습</div>
          <div>
            <div class="ule-brand__name">통합 학습 엔진</div>
            <div class="ule-brand__meta">안정적인 학습 시스템 · v1.06</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
