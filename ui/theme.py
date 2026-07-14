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
        <div class="ule-brand" aria-label="Universal Learning Engine">
          <div class="ule-brand__mark">ULE</div>
          <div>
            <div class="ule-brand__name">Universal Learning Engine</div>
            <div class="ule-brand__meta">STABLE LEARNING SYSTEM · v1.0</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
