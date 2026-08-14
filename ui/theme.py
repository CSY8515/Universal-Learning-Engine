"""Trusted static theme loading for the official ULE interface."""

from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path
import re
from typing import Any, Mapping

from .interface import get_ui_compatibility_layer


_STYLE_PATH = Path(__file__).resolve().parent.parent / "assets" / "ule.css"


@dataclass(frozen=True)
class FeatureWorldDefinition:
    """Presentation identity for one existing functional World."""

    view: str
    slug: str
    label: str
    description: str
    place: str
    motif: str


@dataclass(frozen=True)
class ThemeWorldDefinition:
    """Resolved Ultra Brain Theme World consumed by both ULE renderers."""

    theme_id: str
    source_world_id: str
    revision: int
    home_asset: str
    metaphor: str
    material: str
    lighting: str


FEATURE_WORLD_DEFINITIONS = {
    "Learning": FeatureWorldDefinition(
        "Learning", "w01", "학습", "새로운 지식을 발견하고 이해를 완성하는 세계", "배움의 정원", "✎"
    ),
    "Recovery": FeatureWorldDefinition(
        "Recovery", "w02", "회복 학습", "틀린 기억을 다시 돌보고 더 단단하게 연결하는 세계", "회복의 온실", "↻"
    ),
    "Challenge": FeatureWorldDefinition(
        "Challenge", "w03", "도전 학습", "실력을 시험하고 더 높은 단계에 도전하는 세계", "도전의 성소", "◆"
    ),
    "Analytics": FeatureWorldDefinition(
        "Analytics", "w04", "학습 분석", "쌓인 기록에서 성장의 방향을 발견하는 세계", "통찰의 관측소", "▥"
    ),
    "AI": FeatureWorldDefinition(
        "AI", "w05", "인공지능", "질문과 추천으로 다음 학습을 함께 설계하는 세계", "지혜의 수목원", "✦"
    ),
    "Planner": FeatureWorldDefinition(
        "Planner", "w06", "학습 계획", "오늘의 목표와 앞으로의 일정을 이어 놓는 세계", "시간의 정원", "◷"
    ),
    "Library": FeatureWorldDefinition(
        "Library", "w07", "학습 자료실", "학습에서 태어난 자료와 노트를 보관하는 세계", "기억의 도서관", "▤"
    ),
    "Management": FeatureWorldDefinition(
        "Management", "w08", "관리", "과목과 설정, 연결 정보를 안전하게 돌보는 세계", "세계 관리소", "⚙"
    ),
    "My Learning": FeatureWorldDefinition(
        "My Learning", "w09", "나의 학습", "모든 여정의 기록과 성장을 한눈에 만나는 세계", "성장의 기록원", "◎"
    ),
}

# Backward-compatible read-only projection used by the v1.07 presentation
# tests. The actual renderer consumes FEATURE_WORLD_DEFINITIONS directly.
WORLD_PRESENTATION = {
    view: (
        definition.slug,
        definition.label,
        definition.description,
        definition.place,
    )
    for view, definition in FEATURE_WORLD_DEFINITIONS.items()
}

THEME_WORLD_DEFINITIONS = {
    "official": ("theme-official.png", "knowledge-tree", "obsidian-gold", "stellar-amber"),
    "light": ("theme-light.png", "luminous-atlas", "ivory-glass", "daylight"),
    "dark": ("theme-dark.png", "night-archive", "smoked-glass", "moonlight"),
    "calm": ("theme-calm.png", "quiet-garden", "mist-glass", "diffused"),
    "universe": ("theme-universe.png", "cosmic-canopy", "astral-glass", "nebula"),
    "ecosystem": ("theme-ecosystem.png", "living-canopy", "verdant-glass", "forest-glow"),
    "ocean": ("theme-ocean.png", "tide-knowledge", "aqua-glass", "caustic-blue"),
    "grassland": ("theme-grassland.png", "learning-meadow", "moss-glass", "sunlit-green"),
    "lava": ("theme-lava.png", "forge-of-mastery", "volcanic-glass", "ember"),
    "galaxy": ("theme-galaxy.png", "nebula-bloom", "crystal-glass", "magenta-starlight"),
    "minimal": ("theme-minimal.png", "clear-path", "neutral-glass", "soft-white"),
    "paper": ("theme-paper.png", "scholar-atlas", "vellum-glass", "warm-paper"),
    "archive": ("theme-archive.png", "memory-vault", "bronze-glass", "antique-gold"),
}

# These are the already approved Ultra Brain world ids.  ULE reuses its
# repository-owned functional Worlds and changes the surrounding visual
# language through the shared contract; it does not create a second editor or
# copy another application's binary assets.
THEME_PALETTES = {
    "official": {},
    "light": {
        "background": "#f4f1e8", "background_alt": "#ebe5d8",
        "surface": "rgba(255,255,255,.86)", "surface_strong": "rgba(255,255,255,.96)",
        "text": "#211f19", "muted": "#777164", "accent": "#8c6a27",
        "accent_secondary": "#657b45", "border": "rgba(111,91,50,.22)",
        "border_accent": "rgba(111,91,50,.48)", "focus": "rgba(140,106,39,.58)",
        "gold": "#a67c2d", "gold_soft": "#8c6a27",
    },
    "dark": {
        "background": "#02070b", "background_alt": "#07100f",
        "surface": "rgba(10,17,16,.82)", "surface_strong": "rgba(13,22,19,.94)",
        "text": "#edf5ed", "muted": "#9eafa2", "accent": "#9bb59c",
        "accent_secondary": "#e2f0df", "border": "rgba(142,185,153,.34)",
        "border_accent": "rgba(142,185,153,.58)", "focus": "rgba(226,240,223,.66)",
        "gold": "#e2f0df", "gold_soft": "#9bb59c",
    },
    "calm": {
        "background": "#0d1f26", "background_alt": "#11282f",
        "surface": "rgba(17,40,47,.82)", "surface_strong": "rgba(20,49,56,.95)",
        "text": "#f3f8f7", "muted": "#b8cecc", "accent": "#82aaa8",
        "accent_secondary": "#edf7f5", "border": "rgba(151,190,187,.36)",
        "border_accent": "rgba(151,190,187,.60)", "focus": "rgba(237,247,245,.68)",
        "gold": "#edf7f5", "gold_soft": "#82aaa8",
    },
    "universe": {
        "background": "#08081b", "background_alt": "#0e0c27",
        "surface": "rgba(14,12,39,.86)", "surface_strong": "rgba(20,17,54,.96)",
        "text": "#f0efff", "muted": "#aaa8c7", "accent": "#9d91e8",
        "accent_secondary": "#d5ceff", "border": "rgba(157,145,232,.38)",
        "border_accent": "rgba(157,145,232,.62)", "focus": "rgba(213,206,255,.72)",
        "gold": "#d5ceff", "gold_soft": "#9d91e8",
    },
    "ecosystem": {
        "background": "#05130c", "background_alt": "#081c11",
        "surface": "rgba(8,28,17,.86)", "surface_strong": "rgba(11,38,21,.96)",
        "text": "#eff8e9", "muted": "#a8c3aa", "accent": "#79b67b",
        "accent_secondary": "#c4e6af", "border": "rgba(121,182,123,.38)",
        "border_accent": "rgba(121,182,123,.62)", "focus": "rgba(196,230,175,.72)",
        "gold": "#c4e6af", "gold_soft": "#79b67b",
    },
    "ocean": {
        "background": "#031018", "background_alt": "#041924",
        "surface": "rgba(4,25,36,.88)", "surface_strong": "rgba(5,34,48,.97)",
        "text": "#edfaff", "muted": "#9bc1cc", "accent": "#56b8cf",
        "accent_secondary": "#b8f0fa", "border": "rgba(86,184,207,.40)",
        "border_accent": "rgba(86,184,207,.66)", "focus": "rgba(184,240,250,.72)",
        "gold": "#b8f0fa", "gold_soft": "#56b8cf",
    },
    "grassland": {
        "background": "#232f1a", "background_alt": "#324323",
        "surface": "rgba(50,67,35,.78)", "surface_strong": "rgba(62,82,43,.94)",
        "text": "#f7f8df", "muted": "#d5dfbd", "accent": "#668744",
        "accent_secondary": "#b6dc7a", "border": "rgba(170,207,112,.42)",
        "border_accent": "rgba(182,220,122,.68)", "focus": "rgba(246,248,223,.72)",
        "gold": "#b6dc7a", "gold_soft": "#668744",
    },
    "lava": {
        "background": "#1c0805", "background_alt": "#2b0c07",
        "surface": "rgba(43,12,7,.88)", "surface_strong": "rgba(58,16,9,.97)",
        "text": "#fff1e7", "muted": "#d2a897", "accent": "#e87943",
        "accent_secondary": "#ffc08e", "border": "rgba(232,121,67,.44)",
        "border_accent": "rgba(255,192,142,.70)", "focus": "rgba(255,192,142,.76)",
        "gold": "#ffc08e", "gold_soft": "#e87943",
    },
    "galaxy": {
        "background": "#180819", "background_alt": "#230a21",
        "surface": "rgba(35,10,33,.88)", "surface_strong": "rgba(49,13,45,.97)",
        "text": "#fff0f8", "muted": "#c9a7bc", "accent": "#df86b8",
        "accent_secondary": "#ffc7e5", "border": "rgba(223,134,184,.42)",
        "border_accent": "rgba(255,199,229,.68)", "focus": "rgba(255,199,229,.74)",
        "gold": "#ffc7e5", "gold_soft": "#df86b8",
    },
    "minimal": {
        "background": "#0e1111", "background_alt": "#161a19",
        "surface": "rgba(22,26,25,.86)", "surface_strong": "rgba(30,35,33,.97)",
        "text": "#f5f7f3", "muted": "#a7afaa", "accent": "#d2d7d0",
        "accent_secondary": "#ffffff", "border": "rgba(210,215,208,.30)",
        "border_accent": "rgba(255,255,255,.58)", "focus": "rgba(255,255,255,.70)",
        "gold": "#ffffff", "gold_soft": "#d2d7d0",
    },
    "paper": {
        "background": "#f5ebd3", "background_alt": "#fff8e6",
        "surface": "rgba(255,248,230,.88)", "surface_strong": "rgba(255,252,241,.97)",
        "text": "#3c2c20", "muted": "#765f4c", "accent": "#9b6b3d",
        "accent_secondary": "#5e3e23", "border": "rgba(123,87,53,.34)",
        "border_accent": "rgba(123,87,53,.60)", "focus": "rgba(94,62,35,.68)",
        "gold": "#5e3e23", "gold_soft": "#9b6b3d",
    },
    "archive": {
        "background": "#16110c", "background_alt": "#1f1811",
        "surface": "rgba(31,24,17,.88)", "surface_strong": "rgba(42,32,22,.97)",
        "text": "#f2e9da", "muted": "#b7a994", "accent": "#b49b78",
        "accent_secondary": "#e6d7b8", "border": "rgba(180,155,120,.40)",
        "border_accent": "rgba(230,215,184,.68)", "focus": "rgba(230,215,184,.74)",
        "gold": "#e6d7b8", "gold_soft": "#b49b78",
    },
}
_SAFE_THEME_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_SAFE_WORLD_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_CONTRACT_ID = "ultra-brain.ui/v1"
_INTERFACE_VERSION = "1.0"
_TARGETS = frozenset(
    {
        "ultra-brain",
        "os-ecosystem",
        "living-os",
        "universal-learning-engine",
        "project",
        "module",
        "feature",
    }
)
_PROPAGATION_STATES = frozenset(
    {"automatic", "applied", "locked", "override", "locked-override"}
)
_LOCK_KEYS = frozenset(
    {
        "position",
        "size",
        "background",
        "layout",
        "color",
        "texture",
        "lighting",
        "component",
        "layer",
        "theme",
        "all",
    }
)
_PROPAGATION_TARGETS = frozenset(
    {
        "theme",
        "background",
        "color",
        "brightness",
        "contrast",
        "saturation",
        "hue",
        "texture",
        "lighting",
        "shadow",
        "glow",
        "transparency",
        "blur",
        "layout",
        "componentPosition",
        "componentSize",
        "visibility",
        "animation",
    }
)
_SYSTEM_KEYS = frozenset(
    {"os-ecosystem", "living-os", "universal-learning-engine"}
)
_SYSTEM_ALIASES = {
    "os-ecosystem": "os-ecosystem",
    "os_ecosystem": "os-ecosystem",
    "living-os": "living-os",
    "living_os": "living-os",
    "universal-learning-engine": "universal-learning-engine",
    "universal_learning_engine": "universal-learning-engine",
}
_ADJUSTMENT_LIMITS = {
    "brightness": (0.7, 1.3), "contrast": (0.7, 1.4),
    "saturation": (0.5, 1.5), "hue": (-30.0, 30.0),
    "lighting": (0.0, 1.5), "shadow": (0.4, 1.6),
    "glow": (0.0, 1.8), "texture": (0.0, 1.5),
    "blur": (0.0, 8.0), "transparency": (0.45, 1.0),
}
APPLIED_QUERY_CONTRACT_SESSION_KEY = "ule_applied_query_contract_v1"
_SELF_SYSTEM_ID = "universal-learning-engine"
_APPLIED_PRESENTATION_KEYS = ("theme", "world", "revision", *_ADJUSTMENT_LIMITS)


def _query_scalar(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    return ("" if value is None else str(value)).strip()[:128]


def _bounded_adjustment(values: Mapping[str, Any], name: str) -> float | None:
    raw = _query_scalar(values.get(name))
    if not raw:
        return None
    try:
        number = float(raw)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    minimum, maximum = _ADJUSTMENT_LIMITS[name]
    return max(minimum, min(maximum, number))


def _safe_bool(value: Any) -> bool:
    return _query_scalar(value).casefold() in {"1", "true", "yes", "on"}


def _safe_csv(value: Any, allowed: frozenset[str]) -> tuple[str, ...]:
    result: list[str] = []
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)[:64]
    else:
        items = ("" if value is None else str(value)).strip()[:1024].split(",")
    for item in items:
        candidate = str(item).strip()
        if candidate in allowed and candidate not in result:
            result.append(candidate)
    return tuple(result)


def _safe_system_csv(value: Any) -> tuple[str, ...]:
    """Accept legacy session ids but expose canonical propagation ids."""

    result: list[str] = []
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)[:64]
    else:
        items = ("" if value is None else str(value)).strip()[:1024].split(",")
    for item in items:
        canonical = _SYSTEM_ALIASES.get(str(item).strip().lower())
        if canonical in _SYSTEM_KEYS and canonical not in result:
            result.append(canonical)
    return tuple(result)


def query_contract_from_mapping(
    params: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize the bounded Ultra Brain query contract for this render only.

    The returned mapping contains presentation metadata only. It is deliberately
    not written to learner state, routes, repositories, or business storage.
    """

    values = dict(params or {})
    if _query_scalar(values.get("source")) != "ultra-brain":
        return {}
    contract_id = _query_scalar(values.get("contract")) or _CONTRACT_ID
    interface = _query_scalar(values.get("interface")) or _INTERFACE_VERSION
    if contract_id != _CONTRACT_ID or interface != _INTERFACE_VERSION:
        return {}

    theme_id = _query_scalar(values.get("theme")).lower()
    if not _SAFE_THEME_ID.fullmatch(theme_id) or theme_id not in THEME_PALETTES:
        return {}

    world = _query_scalar(values.get("world")).lower()
    if world and not _SAFE_WORLD_ID.fullmatch(world):
        world = ""
    try:
        revision = max(1, min(2_147_483_647, int(_query_scalar(values.get("revision")) or "1")))
    except ValueError:
        revision = 1

    target = _query_scalar(values.get("target"))
    if target not in _TARGETS:
        target = "universal-learning-engine"
    propagation = _query_scalar(values.get("propagation"))
    if propagation not in _PROPAGATION_STATES:
        propagation = "automatic"

    normalized: dict[str, Any] = {
        "source": "ultra-brain",
        "contract": _CONTRACT_ID,
        "interface": _INTERFACE_VERSION,
        "theme": theme_id,
        "world": world,
        "revision": revision,
        "target": target,
        "propagation": propagation,
        "locks": _safe_csv(values.get("locks"), _LOCK_KEYS),
        "override": _safe_bool(values.get("override")),
        "os_locked": _safe_bool(values.get("os_locked")),
        "os_override": _safe_bool(values.get("os_override")),
        "applied_targets": _safe_csv(values.get("applied_targets"), _PROPAGATION_TARGETS),
        "locked_targets": _safe_csv(values.get("locked_targets"), _PROPAGATION_TARGETS),
        "overridden_targets": _safe_csv(values.get("overridden_targets"), _PROPAGATION_TARGETS),
        "locked_systems": _safe_system_csv(values.get("locked_systems")),
        "overridden_systems": _safe_system_csv(values.get("overridden_systems")),
    }
    for name in _ADJUSTMENT_LIMITS:
        number = _bounded_adjustment(values, name)
        if number is not None:
            normalized[name] = number
    return normalized


def resolve_applied_query_contract(
    incoming: Mapping[str, Any] | None,
    previous_applied: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Resolve ULE presentation precedence without touching business state.

    A ULE-specific lock or override keeps the previous theme, World id,
    revision, and ten visual adjustments. If this Streamlit session has no
    previous accepted contract, the presentation fails closed to Official with
    no propagated adjustments. The boolean reports whether the incoming
    contract is safe to remember as the session's latest applied contract.
    """

    incoming_contract = query_contract_from_mapping(incoming)
    if not incoming_contract:
        return {}, False
    blocked = _SELF_SYSTEM_ID in {
        *incoming_contract["locked_systems"],
        *incoming_contract["overridden_systems"],
    }
    if not blocked:
        return incoming_contract, True

    effective = dict(incoming_contract)
    for name in _ADJUSTMENT_LIMITS:
        effective.pop(name, None)
    previous_contract = query_contract_from_mapping(previous_applied)
    if previous_contract:
        for name in _APPLIED_PRESENTATION_KEYS:
            if name in previous_contract:
                effective[name] = previous_contract[name]
    else:
        effective["theme"] = "official"
        effective["world"] = ""
        effective["revision"] = 1
    return effective, False


def theme_settings_from_mapping(params: Mapping[str, Any] | None) -> dict[str, Any]:
    """Accept only the bounded Ultra Brain theme bridge."""

    contract = query_contract_from_mapping(params)
    if not contract:
        return {}
    theme_id = str(contract["theme"])
    settings: dict[str, Any] = {"theme_id": theme_id}
    if theme_id in {"light", "paper"}:
        settings["mode"] = "light"
    palette = THEME_PALETTES[theme_id]
    if palette:
        settings["colors"] = dict(palette)
    return settings


def resolve_theme_world(
    contract: Mapping[str, Any] | None,
) -> ThemeWorldDefinition:
    """Resolve a bounded Theme World for the Home and Feature renderers."""

    normalized = query_contract_from_mapping(contract)
    theme_id = str(normalized.get("theme", "official"))
    if theme_id not in THEME_WORLD_DEFINITIONS:
        theme_id = "official"
    asset, metaphor, material, lighting = THEME_WORLD_DEFINITIONS[theme_id]
    return ThemeWorldDefinition(
        theme_id=theme_id,
        source_world_id=str(normalized.get("world", "")),
        revision=int(normalized.get("revision", 1)),
        home_asset=asset,
        metaphor=metaphor,
        material=material,
        lighting=lighting,
    )


def query_adjustment_css(params: Mapping[str, Any] | None) -> str:
    """Apply only bounded visual adjustments to existing ULE world art."""

    contract = query_contract_from_mapping(params)
    parsed = {
        name: float(contract[name])
        for name in _ADJUSTMENT_LIMITS
        if name in contract
    }
    if not parsed:
        return ""
    brightness = parsed.get("brightness", 1.0)
    contrast = parsed.get("contrast", 1.0)
    saturation = parsed.get("saturation", 1.0)
    hue = parsed.get("hue", 0.0)
    blur = parsed.get("blur", 0.0)
    transparency = parsed.get("transparency", 1.0)
    preserved_variables = "".join(
        f"--ule-propagated-{name}:{number:.3f};"
        for name, number in parsed.items()
    )
    return (
        '<style data-ultra-brain-adjustments="v1">'
        '.ule-world-backdrop{'
        f"{preserved_variables}"
        f"filter:brightness({brightness:.3f}) contrast({contrast:.3f}) "
        f"saturate({saturation:.3f}) hue-rotate({hue:.3f}deg) "
        f"blur({blur:.3f}px)!important;opacity:{transparency:.3f}!important;"
        "}</style>"
    )


@lru_cache(maxsize=1)
def _official_styles() -> str:
    """Read repository-owned CSS once per process.

    The returned stylesheet is static source-controlled content. Learner topics,
    generated lessons, answers, secrets, and Pack data are never interpolated.
    """

    return _STYLE_PATH.read_text(encoding="utf-8")


def apply_official_theme(
    st_module,
    theme_settings: Mapping[str, Any] | None = None,
) -> None:
    """Apply static official CSS plus validated Ultra Brain token overrides.

    Existing callers pass no settings and therefore receive the exact official
    defaults.  An Ultra Brain host may supply the versioned Theme Contract
    mapping without introducing a second customization screen inside ULE.
    """

    compatibility_css = get_ui_compatibility_layer().render_theme_css(
        theme_settings
    )
    st_module.markdown(
        f"<style>{_official_styles()}\n{compatibility_css}</style>",
        unsafe_allow_html=True,
    )
    st_module.markdown(
        """
        <div class="ule-brand" aria-label="Universal Learning Engine">
            <div class="ule-brand__mark" aria-hidden="true">✦</div>
          <div>
            <div class="ule-brand__name">Universal Learning Engine</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_world_stage(
    st_module,
    selected_view: str,
) -> str:
    """Render the original static scene for one real functional World."""

    definition = FEATURE_WORLD_DEFINITIONS[selected_view]
    st_module.markdown(
        f"""
        <div class="ule-world-backdrop ule-world-backdrop--{definition.slug}"
             aria-hidden="true"></div>
        <section class="ule-world-intro" aria-label="{definition.label}">
          <span class="ule-world-intro__place">{definition.place}</span>
          <h1>{definition.label}</h1>
          <p>{definition.description}</p>
          <span class="ule-world-intro__line" aria-hidden="true"></span>
        </section>
        """,
        unsafe_allow_html=True,
    )
    return definition.slug
