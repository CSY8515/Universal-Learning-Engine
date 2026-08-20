"""Trusted static theme loading for the official ULE interface."""

from dataclasses import dataclass
from html import escape
import math
from pathlib import Path
import re
from typing import Any, Mapping

from .interface import get_ui_compatibility_layer


_STYLE_PATH = Path(__file__).resolve().parent.parent / "assets" / "ule.css"
_STATIC_ROOT = _STYLE_PATH.parent.parent / "static"
FEATURE_BACKGROUND_RESOLVER_VERSION = "1.099"


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
    visual_theme_id: str = "official"
    asset_state: str = "official"
    theme_asset_required: bool = False
    role_asset_revision: int = 0
    central_asset: str = ""
    navigation_skin_asset: str = ""


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
_ROLE_ASSET_REGISTRY = "ui-theme-registry"
_ROLE_ASSET_REGISTRY_VERSION = "1.0.0"
_VISUAL_ROLES = frozenset(
    {
        "HOME_BACKGROUND", "CENTRAL_WORLD", "NAVIGATION_OBJECT_SKIN",
        "FEATURE_BACKGROUND", "DECORATIVE_VISUAL",
    }
)
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
_APPROVED_ROLE_ASSETS = {
    ("dark", _SELF_SYSTEM_ID, None, "HOME_BACKGROUND"): (
        2,
        "theme-role-assets/dark/home-background.png",
    ),
    ("dark", _SELF_SYSTEM_ID, None, "CENTRAL_WORLD"): (
        2,
        "theme-role-assets/dark/central-world.png",
    ),
    ("dark", _SELF_SYSTEM_ID, None, "NAVIGATION_OBJECT_SKIN"): (
        2,
        "theme-role-assets/dark/navigation-object-skin.png",
    ),
    ("dark", _SELF_SYSTEM_ID, "planner", "FEATURE_BACKGROUND"): (
        2,
        "theme-role-assets/dark/learning-plan-background.png",
    ),
    ("dark", _SELF_SYSTEM_ID, "analytics", "FEATURE_BACKGROUND"): (
        2,
        "theme-role-assets/dark/analytics-background.png",
    ),
    **{
        ("dark", _SELF_SYSTEM_ID, feature_id, "FEATURE_BACKGROUND"): (
            2,
            f"theme-role-assets/dark/{feature_id}-background.png",
        )
        for feature_id in (
            "learning",
            "recovery",
            "challenge",
            "ai",
            "library",
            "management",
            "my-learning",
        )
    },
}
_ROLE_CONTEXT_KEYS = (
    "asset_registry", "asset_registry_version", "project_id", "feature_id",
    "visual_role", "asset_revision",
)
_APPLIED_PRESENTATION_KEYS = (
    "theme", "world", "revision", *_ADJUSTMENT_LIMITS, *_ROLE_CONTEXT_KEYS,
)


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
    if (
        _query_scalar(values.get("asset_registry")) == _ROLE_ASSET_REGISTRY
        and _query_scalar(values.get("asset_registry_version")) == _ROLE_ASSET_REGISTRY_VERSION
    ):
        project_id = _SYSTEM_ALIASES.get(
            _query_scalar(values.get("project_id")).lower()
        )
        feature_id = _query_scalar(values.get("feature_id")).lower()
        visual_role = _query_scalar(values.get("visual_role")).upper()
        if feature_id and not _SAFE_WORLD_ID.fullmatch(feature_id):
            feature_id = ""
        if project_id == _SELF_SYSTEM_ID and visual_role in _VISUAL_ROLES:
            try:
                asset_revision = max(
                    1,
                    min(
                        2_147_483_647,
                        int(_query_scalar(values.get("asset_revision")) or "1"),
                    ),
                )
            except ValueError:
                asset_revision = 1
            normalized.update(
                {
                    "asset_registry": _ROLE_ASSET_REGISTRY,
                    "asset_registry_version": _ROLE_ASSET_REGISTRY_VERSION,
                    "project_id": project_id,
                    "feature_id": feature_id,
                    "visual_role": visual_role,
                    "asset_revision": asset_revision,
                }
            )
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


def resolve_role_asset_reference(
    contract: Mapping[str, Any] | None,
    visual_role: str,
    feature_id: str | None = None,
) -> tuple[str | None, str, str]:
    """Resolve only ULE-owned approved role assets, otherwise fail closed."""

    normalized = query_contract_from_mapping(contract)
    safe_role = str(visual_role).strip().upper()
    safe_feature = str(feature_id or "").strip().lower()
    context_matches = (
        normalized.get("asset_registry") == _ROLE_ASSET_REGISTRY
        and normalized.get("project_id") == _SELF_SYSTEM_ID
        and normalized.get("visual_role") == safe_role
        and normalized.get("feature_id", "") == safe_feature
    )
    theme_id = str(normalized.get("theme", "official"))
    if (
        theme_id == "official"
        and safe_role == "HOME_BACKGROUND"
        and not safe_feature
    ):
        return THEME_WORLD_DEFINITIONS["official"][0], "official-default", "NONE"
    if context_matches:
        registered = _approved_role_asset(
            theme_id,
            safe_role,
            safe_feature or None,
            int(normalized.get("asset_revision", 0)),
        )
        if registered:
            source = "theme-project-feature-role" if safe_feature else "theme-project-role"
            return registered, source, "NONE"
    return None, "missing-role-asset", "ASSET REQUIRED"


def _approved_role_asset(
    theme_id: str,
    visual_role: str,
    feature_id: str | None,
    asset_revision: int,
) -> str | None:
    """Return one verified ULE-owned role asset without changing resolution rules."""

    registered = _APPROVED_ROLE_ASSETS.get(
        (theme_id, _SELF_SYSTEM_ID, feature_id, visual_role)
    )
    if not registered or registered[0] > asset_revision:
        return None
    reference = registered[1]
    return reference if (_STATIC_ROOT / reference).is_file() else None


def resolve_theme_world(
    contract: Mapping[str, Any] | None,
) -> ThemeWorldDefinition:
    """Resolve a bounded Theme World for the Home and Feature renderers."""

    normalized = query_contract_from_mapping(contract)
    theme_id = str(normalized.get("theme", "official"))
    if theme_id not in THEME_WORLD_DEFINITIONS:
        theme_id = "official"
    requested_asset, metaphor, material, lighting = THEME_WORLD_DEFINITIONS[theme_id]
    resolved_asset, source, _fallback = resolve_role_asset_reference(
        normalized, "HOME_BACKGROUND"
    )
    role_asset_revision = int(normalized.get("asset_revision", 0))
    if resolved_asset is None and theme_id != "official":
        # A valid project/feature role context belongs to the same approved
        # Theme package as its Home asset. Validate that exact incoming role
        # first, then activate the package Home without weakening per-role
        # resolution or accepting transported file paths.
        incoming_role = str(normalized.get("visual_role", ""))
        incoming_feature = str(normalized.get("feature_id", "")) or None
        context_asset, context_source, _context_fallback = resolve_role_asset_reference(
            normalized,
            incoming_role,
            incoming_feature,
        )
        if context_asset is not None:
            resolved_asset = _approved_role_asset(
                theme_id,
                "HOME_BACKGROUND",
                None,
                role_asset_revision,
            )
            if resolved_asset is not None:
                source = context_source
    resolved_theme_asset = theme_id == "official" or resolved_asset is not None
    visual_theme_id = theme_id if resolved_theme_asset else "official"
    visual_asset = resolved_asset or THEME_WORLD_DEFINITIONS[visual_theme_id][0]
    asset_state = "official" if theme_id == "official" else (
        source if resolved_asset is not None else "fallback-used"
    )
    central_asset = ""
    navigation_skin_asset = ""
    if resolved_asset is not None and theme_id != "official":
        central_asset = _approved_role_asset(
            theme_id, "CENTRAL_WORLD", None, role_asset_revision
        ) or ""
        navigation_skin_asset = _approved_role_asset(
            theme_id, "NAVIGATION_OBJECT_SKIN", None, role_asset_revision
        ) or ""
    return ThemeWorldDefinition(
        theme_id=theme_id,
        source_world_id=str(normalized.get("world", "")),
        revision=int(normalized.get("revision", 1)),
        home_asset=visual_asset,
        metaphor=metaphor,
        material=material,
        lighting=lighting,
        visual_theme_id=visual_theme_id,
        asset_state=asset_state,
        theme_asset_required=theme_id != "official" and resolved_asset is None,
        role_asset_revision=role_asset_revision,
        central_asset=central_asset,
        navigation_skin_asset=navigation_skin_asset,
    )


def resolve_feature_background(
    theme_world: ThemeWorldDefinition,
    selected_view: str,
) -> tuple[str, str, str]:
    """Resolve one deterministic Feature background with an explicit fallback."""

    definition = FEATURE_WORLD_DEFINITIONS[selected_view]
    official_asset = f"worlds/{definition.slug}.png"
    if (
        theme_world.visual_theme_id == theme_world.theme_id
        and theme_world.theme_id != "official"
        and theme_world.role_asset_revision > 0
    ):
        registered = _approved_role_asset(
            theme_world.theme_id,
            "FEATURE_BACKGROUND",
            definition.view.lower().replace(" ", "-"),
            theme_world.role_asset_revision,
        )
        if registered:
            return registered, "theme-project-feature-role", "NONE"
        return official_asset, "official-feature-fallback", "ASSET REQUIRED"
    return official_asset, "official", "NONE"


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


def _official_styles() -> str:
    """Read the current repository-owned CSS for every Streamlit rerun.

    Streamlit Cloud keeps Python processes alive between deployments, so caching
    this file can preserve an obsolete background rule after a release. The
    stylesheet is small, static, and source controlled; reading it again avoids
    cross-release visual leakage without involving learner or secret data.
    """

    return _STYLE_PATH.read_text(encoding="utf-8")


def apply_official_theme(
    st_module,
    theme_settings: Mapping[str, Any] | None = None,
    inherited_effect_css: str = "",
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
        f"<style>{_official_styles()}\n{compatibility_css}\n{inherited_effect_css}</style>",
        unsafe_allow_html=True,
    )
    st_module.markdown(
        """
        <style data-ultra-brain-theme-bleed="v1">
        .ule-world-backdrop{inset:0!important;width:100vw!important;height:100vh!important}
        body:has(.ule-world-theme--light),body:has(.ule-world-theme--paper){--ule-color-text:#3c2c20;--ule-color-muted:#765f4c;--ule-color-accent:#9b6b3d;--ule-color-gold:#9b6b3d}
        body:has(.ule-world-theme--dark),body:has(.ule-world-theme--minimal),body:has(.ule-world-theme--archive){--ule-color-accent:#b49b78;--ule-color-gold:#b49b78}
        body:has(.ule-world-theme--calm){--ule-color-accent:#82aaa8;--ule-color-gold:#82aaa8}
        body:has(.ule-world-theme--universe){--ule-color-accent:#9d91e8;--ule-color-gold:#9d91e8}
        body:has(.ule-world-theme--ecosystem){--ule-color-accent:#79b67b;--ule-color-gold:#79b67b}
        body:has(.ule-world-theme--ocean){--ule-color-accent:#56b8cf;--ule-color-gold:#56b8cf}
        body:has(.ule-world-theme--grassland){--ule-color-accent:#668744;--ule-color-gold:#668744}
        body:has(.ule-world-theme--lava){--ule-color-accent:#e87943;--ule-color-gold:#e87943}
        body:has(.ule-world-theme--galaxy){--ule-color-accent:#df86b8;--ule-color-gold:#df86b8}
        </style>
        """,
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
    theme_world: ThemeWorldDefinition | str = "official",
) -> str:
    """Render a Theme-aware Scene for one real functional World."""

    definition = FEATURE_WORLD_DEFINITIONS[selected_view]
    if isinstance(theme_world, ThemeWorldDefinition):
        resolved_world = theme_world
    else:
        theme_id = theme_world if theme_world in THEME_WORLD_DEFINITIONS else "official"
        _requested_asset, metaphor, material, lighting = THEME_WORLD_DEFINITIONS[theme_id]
        visual_theme_id = theme_id if theme_id == "official" else "official"
        asset = THEME_WORLD_DEFINITIONS[visual_theme_id][0]
        resolved_world = ThemeWorldDefinition(
            theme_id,
            "",
            1,
            asset,
            metaphor,
            material,
            lighting,
            visual_theme_id,
            "official" if theme_id == "official" else "fallback-used",
            theme_id != "official",
        )
    safe_theme = escape(resolved_world.theme_id, quote=True)
    safe_visual_theme = escape(resolved_world.visual_theme_id, quote=True)
    safe_asset_state = escape(resolved_world.asset_state, quote=True)
    safe_source_world = escape(resolved_world.source_world_id, quote=True)
    feature_asset, feature_asset_state, feature_fallback = resolve_feature_background(
        resolved_world,
        selected_view,
    )
    feature_asset_url = escape(f"./app/static/{feature_asset}", quote=True)
    feature_asset_style = f' style="--ule-feature-image:url(\'{feature_asset_url}\');"'
    st_module.markdown(
        f"""
        <div class="ule-world-backdrop ule-world-backdrop--{definition.slug} ule-world-theme--{safe_visual_theme}"
             data-theme-world="{safe_theme}"
             data-theme-visual="{safe_visual_theme}"
             data-theme-asset-state="{safe_asset_state}"
             data-theme-asset-required="{str(resolved_world.theme_asset_required).lower()}"
             data-theme-source-world="{safe_source_world}"
             data-theme-revision="{resolved_world.revision}"
             data-feature-role-asset="{str(feature_asset_state == 'theme-project-feature-role').lower()}"
             data-feature-asset-state="{escape(feature_asset_state, quote=True)}"
             data-feature-asset-required="{str(feature_fallback == 'ASSET REQUIRED').lower()}"{feature_asset_style}
             aria-hidden="true"></div>
        <section class="ule-world-intro ule-world-intro--{definition.slug}"
                 data-feature-world="{definition.slug}"
                 aria-label="{definition.label}">
          <span class="ule-world-intro__motif" aria-hidden="true">{definition.motif}</span>
          <span class="ule-world-intro__place">{definition.place}</span>
          <h1>{definition.label}</h1>
          <p>{definition.description}</p>
          <span class="ule-world-intro__line" aria-hidden="true"></span>
        </section>
        """,
        unsafe_allow_html=True,
    )
    return definition.slug
