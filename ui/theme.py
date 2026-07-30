"""Trusted static theme loading for the official ULE interface."""

from functools import lru_cache
from pathlib import Path


_STYLE_PATH = Path(__file__).resolve().parent.parent / "assets" / "ule.css"
WORLD_PRESENTATION = {
    "Learning": ("w01", "학습", "새로운 지식을 발견하고 이해를 완성하는 세계", "배움의 정원"),
    "Recovery": ("w02", "회복 학습", "틀린 기억을 다시 돌보고 더 단단하게 연결하는 세계", "회복의 온실"),
    "Challenge": ("w03", "도전 학습", "실력을 시험하고 더 높은 단계에 도전하는 세계", "도전의 성소"),
    "Analytics": ("w04", "학습 분석", "쌓인 기록에서 성장의 방향을 발견하는 세계", "통찰의 관측소"),
    "AI": ("w05", "인공지능", "질문과 추천으로 다음 학습을 함께 설계하는 세계", "지혜의 수목원"),
    "Planner": ("w06", "학습 계획", "오늘의 목표와 앞으로의 일정을 이어 놓는 세계", "시간의 정원"),
    "Library": ("w07", "학습 자료실", "학습에서 태어난 자료와 노트를 보관하는 세계", "기억의 도서관"),
    "Management": ("w08", "관리", "과목과 설정, 연결 정보를 안전하게 돌보는 세계", "세계 관리소"),
    "My Learning": ("w09", "나의 학습", "모든 여정의 기록과 성장을 한눈에 만나는 세계", "성장의 기록원"),
}


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
            <div class="ule-brand__mark" aria-hidden="true">✦</div>
          <div>
            <div class="ule-brand__name">Universal Learning Engine</div>
            <div class="ule-brand__meta">공식 학습 세계 · v1.07</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_world_stage(st_module, selected_view: str) -> str:
    """Render trusted static presentation chrome for one functional World."""

    slug, label, description, place = WORLD_PRESENTATION[selected_view]
    st_module.markdown(
        f"""
        <div class="ule-world-backdrop ule-world-backdrop--{slug}"
             aria-hidden="true"></div>
        <section class="ule-world-intro" aria-label="{label}">
          <span class="ule-world-intro__place">{place}</span>
          <h1>{label}</h1>
          <p>{description}</p>
          <span class="ule-world-intro__line" aria-hidden="true"></span>
        </section>
        """,
        unsafe_allow_html=True,
    )
    return slug
