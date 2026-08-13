"""Safe Ultra Brain world-theme propagation for the ULE presentation layer.

Ultra Brain owns editing.  This module only accepts its closed query contract,
resolves ULE lock/override rules, and translates the selected world package to
the existing v1.09 theme interface.  It never exposes a downstream UI Studio.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import Any, Mapping


THEME_KEYS = (
    "official",
    "light",
    "dark",
    "universe",
    "galaxy",
    "ecosystem",
    "ocean",
    "grassland",
    "lava",
    "minimal",
    "paper",
    "archive",
    "calm",
)
PROPAGATION_TARGETS = (
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
)
ADJUSTMENT_RANGES = {
    "brightness": (0.7, 1.3, 1.0),
    "contrast": (0.7, 1.4, 1.0),
    "saturation": (0.5, 1.5, 1.0),
    "hue": (-30.0, 30.0, 0.0),
    "lighting": (0.0, 1.5, 1.0),
    "shadow": (0.4, 1.6, 1.0),
    "glow": (0.0, 1.8, 1.0),
    "texture": (0.0, 1.5, 1.0),
    "blur": (0.0, 8.0, 0.0),
    "transparency": (0.45, 1.0, 1.0),
}
_SAFE_TOKEN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_JSON_LIMIT = 4096
_NODE_ID = "universal-learning-engine"
_CONTRACT_ID = "ultra-brain.ui/v1"
_INTERFACE_VERSION = "1.0"
_SOURCE_ID = "ultra-brain"
_ACCEPTED_TARGETS = frozenset({"os-ecosystem", _NODE_ID, "project"})
_ACCEPTED_SCOPES = frozenset(
    {"all", "global", _NODE_ID, "project", "module", "feature"}
)
_PROPAGATION_STATES = frozenset(
    {"automatic", "applied", "locked", "override", "locked-override"}
)
_WORLD_IDS = {
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
_LAYOUT_KEYS = ("topbar", "center", "seed", "rail")
_LAYOUT_GROUPS = frozenset({"core", "navigation", "ecosystem"})
_UI_LOCK_TARGETS: dict[str, tuple[str, ...]] = {
    "position": ("componentPosition",),
    "size": ("componentSize",),
    "background": ("background",),
    "layout": ("layout",),
    "color": ("color",),
    "texture": ("texture",),
    "lighting": ("lighting",),
    "component": ("componentPosition", "componentSize", "visibility"),
    "layer": ("visibility",),
}
_LAYOUT_DEFAULTS: dict[str, dict[str, object]] = {
    "topbar": {
        "x": 0.0,
        "y": 0.0,
        "scale": 1.0,
        "visible": True,
        "pinned": True,
        "group": "core",
    },
    "center": {
        "x": 0.0,
        "y": 0.0,
        "scale": 1.0,
        "visible": True,
        "pinned": False,
        "group": "core",
    },
    "seed": {
        "x": 0.0,
        "y": 0.0,
        "scale": 1.0,
        "visible": True,
        "pinned": False,
        "group": "ecosystem",
    },
    "rail": {
        "x": 0.0,
        "y": 0.0,
        "scale": 1.0,
        "visible": True,
        "pinned": False,
        "group": "navigation",
    },
}


# These are presentation-only derivatives of the official Ultra Brain theme
# registry.  Every non-official profile owns a repository-local world image.
_PROFILES: dict[str, dict[str, str]] = {
    "light": {"mode": "light", "background": "#d9d5c3", "background_alt": "#ece8d7", "surface": "rgba(239,235,216,.84)", "surface_strong": "rgba(246,243,226,.97)", "text": "#20251f", "muted": "#566057", "accent": "#7a5b25", "bright": "#a47a2f", "border": "rgba(92,75,40,.32)", "radius": "8px", "shadow": "rgba(65,49,26,.22)", "light": "164,122,47"},
    "dark": {"mode": "dark", "background": "#050d10", "background_alt": "#081317", "surface": "rgba(5,13,16,.82)", "surface_strong": "rgba(8,19,23,.96)", "text": "#eef2ed", "muted": "#9eaaa5", "accent": "#83aa8c", "bright": "#bcd3af", "border": "rgba(128,169,146,.30)", "radius": "6px", "shadow": "rgba(0,0,0,.52)", "light": "188,211,175"},
    "universe": {"mode": "dark", "background": "#05051a", "background_alt": "#0e0c27", "surface": "rgba(8,8,27,.80)", "surface_strong": "rgba(14,12,39,.95)", "text": "#f0efff", "muted": "#aaa8c7", "accent": "#9d91e8", "bright": "#d5ceff", "border": "rgba(157,145,232,.35)", "radius": "7px", "shadow": "rgba(5,3,26,.58)", "light": "157,145,232"},
    "galaxy": {"mode": "dark", "background": "#17091e", "background_alt": "#230a21", "surface": "rgba(24,8,25,.80)", "surface_strong": "rgba(35,10,33,.95)", "text": "#fff0f8", "muted": "#c9a7bc", "accent": "#df86b8", "bright": "#ffc7e5", "border": "rgba(223,134,184,.34)", "radius": "9px", "shadow": "rgba(25,2,25,.56)", "light": "255,199,229"},
    "ecosystem": {"mode": "dark", "background": "#03140c", "background_alt": "#081c11", "surface": "rgba(5,19,12,.80)", "surface_strong": "rgba(8,28,17,.95)", "text": "#eff8e9", "muted": "#a8c3aa", "accent": "#79b67b", "bright": "#c4e6af", "border": "rgba(121,182,123,.34)", "radius": "6px", "shadow": "rgba(0,18,7,.52)", "light": "196,230,175"},
    "ocean": {"mode": "dark", "background": "#021222", "background_alt": "#041924", "surface": "rgba(3,16,24,.82)", "surface_strong": "rgba(4,25,36,.96)", "text": "#edfaff", "muted": "#9bc1cc", "accent": "#56b8cf", "bright": "#b8f0fa", "border": "rgba(86,184,207,.34)", "radius": "5px", "shadow": "rgba(0,13,25,.58)", "light": "184,240,250"},
    "grassland": {"mode": "light", "background": "#dce8bd", "background_alt": "#f0f4da", "surface": "rgba(226,232,197,.82)", "surface_strong": "rgba(243,246,222,.96)", "text": "#26321f", "muted": "#66735b", "accent": "#668744", "bright": "#a9ce72", "border": "rgba(102,135,68,.32)", "radius": "10px", "shadow": "rgba(48,68,31,.24)", "light": "169,206,114"},
    "lava": {"mode": "dark", "background": "#250702", "background_alt": "#3b0c06", "surface": "rgba(28,8,5,.82)", "surface_strong": "rgba(43,12,7,.96)", "text": "#fff1e7", "muted": "#d2a897", "accent": "#e87943", "bright": "#ffc08e", "border": "rgba(232,121,67,.38)", "radius": "3px", "shadow": "rgba(34,3,0,.62)", "light": "255,192,142"},
    "minimal": {"mode": "dark", "background": "#080b0b", "background_alt": "#111515", "surface": "rgba(14,17,17,.78)", "surface_strong": "rgba(22,26,25,.96)", "text": "#f5f7f3", "muted": "#a7afaa", "accent": "#d2d7d0", "bright": "#ffffff", "border": "rgba(210,215,208,.25)", "radius": "2px", "shadow": "rgba(0,0,0,.44)", "light": "255,255,255"},
    "paper": {"mode": "light", "background": "#dfcfaa", "background_alt": "#f4ead3", "surface": "rgba(246,240,222,.88)", "surface_strong": "rgba(255,252,242,.98)", "text": "#33281e", "muted": "#756454", "accent": "#8b5e34", "bright": "#bd8550", "border": "rgba(139,94,52,.30)", "radius": "1px", "shadow": "rgba(78,48,23,.20)", "light": "189,133,80"},
    "archive": {"mode": "dark", "background": "#120d08", "background_alt": "#1f1811", "surface": "rgba(22,17,12,.82)", "surface_strong": "rgba(31,24,17,.96)", "text": "#f2e9da", "muted": "#b7a994", "accent": "#b49b78", "bright": "#e6d7b8", "border": "rgba(180,155,120,.34)", "radius": "2px", "shadow": "rgba(12,8,4,.58)", "light": "230,215,184"},
    "calm": {"mode": "light", "background": "#b9cbd2", "background_alt": "#dce6e9", "surface": "rgba(218,228,232,.86)", "surface_strong": "rgba(238,243,244,.97)", "text": "#17262e", "muted": "#435c67", "accent": "#547b8c", "bright": "#365f72", "border": "rgba(62,94,108,.45)", "radius": "8px", "shadow": "rgba(44,67,77,.24)", "light": "207,225,232"},
}


def _scalar(query: Mapping[str, object], key: str, default: str = "") -> str:
    value = query.get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[-1] if value else default
    return str(value).strip()


def _safe_token(value: object, default: str = "") -> str:
    candidate = str(value).strip().lower()
    return candidate if _SAFE_TOKEN.fullmatch(candidate) else default


def _safe_json(query: Mapping[str, object], key: str) -> object | None:
    raw = _scalar(query, key)
    if not raw or len(raw) > _JSON_LIMIT:
        return None
    if any(ord(character) < 0x20 for character in raw):
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _normalise_targets(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        candidates = value.split(",")
    elif isinstance(value, (list, tuple)):
        candidates = value
    else:
        return ()
    aliases = {target.casefold(): target for target in PROPAGATION_TARGETS}
    result: list[str] = []
    for item in candidates:
        target = aliases.get(str(item).strip().casefold())
        if target and target not in result:
            result.append(target)
    return tuple(result)


def _node_targets(query: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = _safe_json(query, key)
    if not isinstance(value, dict):
        return ()
    return _normalise_targets(value.get(_NODE_ID, ()))


def _ui_lock_targets(query: Mapping[str, object]) -> tuple[str, ...]:
    """Translate Ultra Brain's editing locks into propagation categories."""

    if "uiLocks" not in query:
        return ()
    value = _safe_json(query, "uiLocks")
    if not isinstance(value, dict):
        raise ValueError("invalid UI lock contract")
    if any(key not in _UI_LOCK_TARGETS for key in value):
        raise ValueError("unknown UI lock")
    if any(not isinstance(enabled, bool) for enabled in value.values()):
        raise ValueError("invalid UI lock value")

    blocked: list[str] = []
    for key, targets in _UI_LOCK_TARGETS.items():
        if value.get(key) is True:
            for target in targets:
                if target not in blocked:
                    blocked.append(target)
    return tuple(blocked)


def _safe_adjustment(query: Mapping[str, object], key: str) -> float:
    minimum, maximum, default = ADJUSTMENT_RANGES[key]
    try:
        value = float(_scalar(query, key, str(default)))
    except (TypeError, ValueError):
        value = default
    if not math.isfinite(value):
        value = default
    return min(maximum, max(minimum, value))


def _truthy(value: object) -> bool:
    return str(value).strip().casefold() in {"1", "true", "yes", "on"}


def _rgba(rgb: str, alpha: float) -> str:
    return f"rgba({rgb},{min(1.0, max(0.0, alpha)):.3f})"


def _finite_clamped(
    value: object,
    minimum: float,
    maximum: float,
    default: float,
) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return min(maximum, max(minimum, number))


def _safe_layout(query: Mapping[str, object]) -> dict[str, dict[str, object]] | None:
    """Return the closed four-slot layout projection or fail closed."""

    if "layout" not in query:
        return None
    raw_layout = _safe_json(query, "layout")
    if not isinstance(raw_layout, dict):
        raise ValueError("invalid layout contract")

    normalized: dict[str, dict[str, object]] = {}
    for key in _LAYOUT_KEYS:
        fallback = _LAYOUT_DEFAULTS[key]
        candidate = raw_layout.get(key, {})
        if not isinstance(candidate, dict):
            candidate = {}
        group = str(candidate.get("group", fallback["group"]))
        normalized[key] = {
            "group": group if group in _LAYOUT_GROUPS else fallback["group"],
            "pinned": candidate.get("pinned") is True,
            "scale": _finite_clamped(
                candidate.get("scale", fallback["scale"]),
                0.72,
                1.32,
                float(fallback["scale"]),
            ),
            "visible": candidate.get("visible") is not False,
            "x": _finite_clamped(
                candidate.get("x", fallback["x"]),
                -80.0,
                80.0,
                float(fallback["x"]),
            ),
            "y": _finite_clamped(
                candidate.get("y", fallback["y"]),
                -60.0,
                60.0,
                float(fallback["y"]),
            ),
        }
    return normalized


def _layout_declarations(
    layout: Mapping[str, Mapping[str, object]] | None,
    *,
    allow_position: bool,
    allow_size: bool,
    allow_visibility: bool,
) -> list[str]:
    """Translate normalized layout values to fixed CSS variables only."""

    if layout is None or not (allow_position or allow_size or allow_visibility):
        return []

    declarations: list[str] = []
    display_types = {
        "topbar": "flex",
        "center": "block",
        "seed": "block",
        "rail": "block",
    }
    for slot in _LAYOUT_KEYS:
        item = layout[slot]
        x = float(item["x"]) if allow_position else 0.0
        y = float(item["y"]) if allow_position else 0.0
        scale = float(item["scale"]) if allow_size else 1.0
        visible = bool(item["visible"]) if allow_visibility else True
        declarations.extend(
            (
                f"  --ule-inherited-{slot}-transform: translate({x:g}px, {y:g}px) scale({scale:g});",
                f"  --ule-inherited-{slot}-display: {display_types[slot] if visible else 'none'};",
            )
        )
    return declarations


@dataclass(frozen=True)
class InheritedTheme:
    """Validated downstream presentation result for one request."""

    theme: str
    world: str
    revision: str
    active_targets: tuple[str, ...]
    blocked_targets: tuple[str, ...]
    settings: Mapping[str, Any] | None
    effect_css: str


def resolve_inherited_theme(
    query: Mapping[str, object],
) -> InheritedTheme | None:
    """Resolve a query contract without changing ULE's no-query baseline."""

    if not query:
        return None

    source = _safe_token(_scalar(query, "source"), "")
    contract = _scalar(query, "contract")
    interface = _scalar(query, "interface")
    target = _safe_token(_scalar(query, "target"), "")
    scope = _safe_token(_scalar(query, "scope"), "")
    propagation = _safe_token(_scalar(query, "propagation"), "")
    if (
        source != _SOURCE_ID
        or contract != _CONTRACT_ID
        or interface != _INTERFACE_VERSION
        or target not in _ACCEPTED_TARGETS
        or scope not in _ACCEPTED_SCOPES
        or propagation not in _PROPAGATION_STATES
    ):
        return None

    requested = _safe_token(_scalar(query, "theme"), "")
    if requested not in THEME_KEYS:
        return None
    theme = requested
    world = _safe_token(_scalar(query, "world"), "")
    revision = _safe_token(_scalar(query, "revision"), "")
    if world != _WORLD_IDS[theme] or not revision:
        return None

    if "propagationTargets" not in query:
        return None
    raw_targets = _safe_json(query, "propagationTargets")
    active_targets = _normalise_targets(raw_targets)
    if not active_targets:
        return None

    for key in ("propagationLocks", "propagationOverrides"):
        if key in query and not isinstance(_safe_json(query, key), dict):
            return None

    blocked = set(_node_targets(query, "propagationLocks"))
    blocked.update(_node_targets(query, "propagationOverrides"))
    try:
        blocked.update(_ui_lock_targets(query))
    except ValueError:
        return None

    # Legacy flat lock fields are honoured only when explicitly targeted at
    # ULE.  OS Ecosystem's own legacy lock must not accidentally freeze ULE.
    if target == _NODE_ID:
        blocked.update(_normalise_targets(_scalar(query, "locks")))
        blocked.update(_normalise_targets(_scalar(query, "locked_targets")))
        blocked.update(_normalise_targets(_scalar(query, "overridden_targets")))
        if _truthy(_scalar(query, "override")):
            blocked.update(active_targets)

    blocked_targets = tuple(
        item for item in PROPAGATION_TARGETS if item in blocked
    )
    active = set(active_targets)

    def allowed(category: str) -> bool:
        return category in active and category not in blocked

    profile = _PROFILES.get(theme)
    settings: dict[str, Any] = {
        "theme_id": f"ultra-brain-{theme}",
        "interface_version": _INTERFACE_VERSION,
    }

    if profile and allowed("color"):
        settings.update(
            {
                "mode": profile["mode"],
                "colors": {
                    "background": profile["background"],
                    "background_alt": profile["background_alt"],
                    "surface": profile["surface"],
                    "surface_strong": profile["surface_strong"],
                    "text": profile["text"],
                    "muted": profile["muted"],
                    "accent": profile["accent"],
                    "accent_secondary": profile["bright"],
                    "border": profile["border"],
                    "border_accent": profile["border"],
                    "focus": profile["bright"],
                    "gold": profile["bright"],
                    "gold_soft": profile["accent"],
                    "success": profile["accent"],
                    "warning": profile["bright"],
                    "error": "#ff8f9b",
                },
                "icons": {
                    "color": profile["text"],
                    "accent": profile["bright"],
                },
            }
        )

    if profile and any(
        allowed(category) for category in ("theme", "color", "shadow", "glow")
    ):
        surfaces: dict[str, str] = {}
        buttons: dict[str, str] = {}
        widgets: dict[str, str] = {}
        if allowed("theme"):
            radius = profile["radius"]
            surfaces.update(
                {
                    "card_radius": radius,
                    "scene_radius": radius,
                    "home_dock_radius": radius,
                    "world_dock_radius": radius,
                    "world_dock_item_radius": radius,
                }
            )
            buttons["radius"] = radius
            widgets["radius"] = radius
        if allowed("color"):
            surfaces.update(
                {
                    "card_background": profile["surface"],
                    "card_border": profile["border"],
                    "scene_border": profile["border"],
                    "home_dock_background": profile["surface_strong"],
                    "home_dock_border": profile["border"],
                    "world_dock_background": profile["surface_strong"],
                    "world_dock_border": profile["border"],
                }
            )
            buttons.update(
                {
                    "background": profile["surface"],
                    "primary_background": profile["accent"],
                    "text": profile["text"],
                    "border": profile["border"],
                    "hint_background": profile["surface_strong"],
                    "hint_border": profile["accent"],
                    "hint_text": profile["text"],
                    "orbit_background": profile["surface"],
                    "orbit_border": profile["border"],
                    "orbit_text": profile["text"],
                }
            )
            widgets.update(
                {
                    "background": profile["surface"],
                    "border": profile["border"],
                    "input_background": profile["surface_strong"],
                    "input_border": profile["border"],
                    "dialog_background": profile["surface_strong"],
                    "dashboard_background": profile["surface"],
                    "metric_background": profile["surface"],
                    "metric_border": profile["border"],
                    "tab_background": profile["surface"],
                    "tab_border": profile["border"],
                }
            )
        if allowed("shadow"):
            surfaces["card_shadow"] = f"0 24px 80px {profile['shadow']}"
            widgets["shadow"] = f"inset 0 1px 0 {_rgba(profile['light'], .08)}"
            buttons["shadow"] = f"inset 0 0 18px {_rgba(profile['light'], .12)}"
        if allowed("glow"):
            surfaces["card_hover_shadow"] = (
                f"0 18px 48px {_rgba(profile['light'], .18)}"
            )
        if surfaces:
            settings["surfaces"] = surfaces
        if buttons:
            settings["buttons"] = buttons
        if widgets:
            settings["widgets"] = widgets

    if profile and allowed("background"):
        image = f'url("./app/static/themes/{theme}.png")'
        settings["backgrounds"] = {
            "world_map": image,
            **{f"w{index:02d}": image for index in range(1, 10)},
        }

    motion_value = _scalar(query, "motion", "true")
    if allowed("animation") and "motion" in query:
        settings["animation"] = {"enabled": _truthy(motion_value)}

    density = _safe_token(_scalar(query, "density"), "")
    if allowed("layout") and density in {"compact", "spacious"}:
        if density == "compact":
            settings["layout"] = {
                "content_padding": ".75rem 1rem 6.5rem",
                "gap": ".75rem",
            }
        else:
            settings["layout"] = {
                "content_padding": "1.35rem 1.75rem 8rem",
                "gap": "1.35rem",
            }

    try:
        layout = _safe_layout(query)
    except ValueError:
        return None

    adjustments = {
        key: _safe_adjustment(query, key) if allowed(key) else default
        for key, (_minimum, _maximum, default) in ADJUSTMENT_RANGES.items()
    }
    declarations: list[str] = []
    effect_targets = tuple(ADJUSTMENT_RANGES)
    has_effect_adjustment = any(
        allowed(key)
        and not math.isclose(adjustments[key], ADJUSTMENT_RANGES[key][2])
        for key in effect_targets
    )
    if has_effect_adjustment:
        light_rgb = profile["light"] if profile else "110,186,255"
        lighting_strength = adjustments["lighting"]
        if lighting_strength > 1:
            light_alpha = min(0.18, (lighting_strength - 1) * 0.36)
            lighting = (
                "radial-gradient(ellipse at 50% 42%, "
                f"{_rgba(light_rgb, light_alpha)}, transparent 58%)"
            )
        else:
            lighting = "linear-gradient(transparent, transparent)"

        texture_strength = adjustments["texture"]
        if texture_strength > 1:
            texture_alpha = min(0.06, (texture_strength - 1) * 0.12)
            texture = (
                f"radial-gradient(circle at 18% 27%, {_rgba(light_rgb, texture_alpha)} 0 .7px, transparent 1.4px) 0 0 / 19px 23px, "
                f"radial-gradient(circle at 71% 64%, {_rgba(light_rgb, texture_alpha * .7)} 0 .6px, transparent 1.3px) 0 0 / 29px 31px"
            )
        else:
            texture = "linear-gradient(transparent, transparent)"

        shadow_strength = adjustments["shadow"]
        if math.isclose(shadow_strength, 1.0):
            content_shadow = "var(--ule-shadow)"
        else:
            content_shadow = (
                f"0 {18 * shadow_strength:g}px {64 * shadow_strength:g}px "
                f"rgba(0,0,0,{min(.72, .34 + shadow_strength * .14):.3f})"
            )

        glow_strength = max(0.0, adjustments["glow"] - 1.0)
        if glow_strength:
            content_glow = (
                f"0 0 {30 * glow_strength:g}px "
                f"{_rgba(light_rgb, min(.24, glow_strength * .24))}"
            )
        else:
            content_glow = "0 0 0 transparent"

        declarations.extend(
            (
                f"  --ule-inherited-brightness: {adjustments['brightness']:g};",
                f"  --ule-inherited-contrast: {adjustments['contrast']:g};",
                f"  --ule-inherited-saturation: {adjustments['saturation']:g};",
                f"  --ule-inherited-hue: {adjustments['hue']:g}deg;",
                f"  --ule-inherited-blur: {adjustments['blur']:g}px;",
                f"  --ule-inherited-opacity: {adjustments['transparency']:g};",
                f"  --ule-inherited-lighting: {lighting};",
                f"  --ule-inherited-texture: {texture};",
                f"  --ule-inherited-content-shadow: {content_shadow};",
                f"  --ule-inherited-content-glow: {content_glow};",
            )
        )

    declarations.extend(
        _layout_declarations(
            layout,
            allow_position=allowed("componentPosition"),
            allow_size=allowed("componentSize"),
            allow_visibility=allowed("visibility"),
        )
    )
    effect_css = (
        "\n".join((":root {", *declarations, "}")) if declarations else ""
    )

    # Official remains repository-native.  The generated effects still allow
    # Ultra Brain's detail sliders to operate without replacing official art.
    if len(settings) == 2:
        settings_value: Mapping[str, Any] | None = None
    else:
        settings_value = settings
    return InheritedTheme(
        theme=theme,
        world=world,
        revision=revision,
        active_targets=tuple(active_targets),
        blocked_targets=blocked_targets,
        settings=settings_value,
        effect_css=effect_css,
    )
