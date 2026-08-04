"""Theme, component, and module registries for the ULE UI foundation."""

from __future__ import annotations

from .contracts import (
    ComponentContract,
    DesignTokens,
    ModuleThemeContract,
    ThemeContract,
    UI_FOUNDATION_INTERFACE_VERSION,
)


class RegistryError(ValueError):
    """Raised for duplicate or unknown UI registry entries."""


class ThemeRegistry:
    """Registry of versioned themes accepted by the compatibility layer."""

    def __init__(self) -> None:
        self._themes: dict[str, ThemeContract] = {}

    def register(self, theme: ThemeContract) -> None:
        if theme.theme_id in self._themes:
            raise RegistryError(f"theme already registered: {theme.theme_id}")
        self._themes[theme.theme_id] = theme

    def resolve(self, theme_id: str) -> ThemeContract:
        try:
            return self._themes[theme_id]
        except KeyError as exc:
            raise RegistryError(f"unknown theme: {theme_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._themes))


class UIRegistry:
    """Closed registry of component and module theme dependencies."""

    def __init__(self) -> None:
        self._components: dict[str, ComponentContract] = {}
        self._modules: dict[str, ModuleThemeContract] = {}

    def register_component(self, contract: ComponentContract) -> None:
        if contract.component_id in self._components:
            raise RegistryError(
                f"component already registered: {contract.component_id}"
            )
        self._components[contract.component_id] = contract

    def register_module(self, contract: ModuleThemeContract) -> None:
        if contract.module_id in self._modules:
            raise RegistryError(f"module already registered: {contract.module_id}")
        missing = sorted(set(contract.components) - set(self._components))
        if missing:
            raise RegistryError(
                f"module {contract.module_id} has unknown components: {', '.join(missing)}"
            )
        self._modules[contract.module_id] = contract

    def component(self, component_id: str) -> ComponentContract:
        try:
            return self._components[component_id]
        except KeyError as exc:
            raise RegistryError(f"unknown component: {component_id}") from exc

    def module(self, module_id: str) -> ModuleThemeContract:
        try:
            return self._modules[module_id]
        except KeyError as exc:
            raise RegistryError(f"unknown module: {module_id}") from exc

    def component_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._components))

    def module_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._modules))


def build_default_theme_registry() -> ThemeRegistry:
    registry = ThemeRegistry()
    registry.register(
        ThemeContract(
            theme_id="ule-official",
            interface_version=UI_FOUNDATION_INTERFACE_VERSION,
            tokens=DesignTokens(),
        )
    )
    return registry


def build_default_ui_registry() -> UIRegistry:
    registry = UIRegistry()
    components = (
        ComponentContract("background", ("backgrounds", "colors")),
        ComponentContract("layout", ("layout",)),
        ComponentContract("header", ("typography", "colors", "icons")),
        ComponentContract("navigation", ("buttons", "icons", "animation")),
        ComponentContract("card", ("surfaces", "colors", "animation")),
        ComponentContract("button", ("buttons", "colors", "animation")),
        ComponentContract("widget", ("widgets", "typography", "colors")),
        ComponentContract("dialog", ("widgets", "surfaces", "colors")),
        ComponentContract("icon", ("icons", "colors")),
        ComponentContract("typography", ("typography", "colors")),
        ComponentContract("animation", ("animation",)),
    )
    for contract in components:
        registry.register_component(contract)

    shared = (
        "background",
        "layout",
        "header",
        "navigation",
        "card",
        "button",
        "widget",
        "dialog",
        "icon",
        "typography",
        "animation",
    )
    module_backgrounds = {
        "Dashboard": "backgrounds.world_map",
        "Learning": "backgrounds.w01",
        "CBT": "backgrounds.w01",
        "Recovery": "backgrounds.w02",
        "Challenge": "backgrounds.w03",
        "Analytics": "backgrounds.w04",
        "Reports": "backgrounds.w04",
        "AI": "backgrounds.w05",
        "Planner": "backgrounds.w06",
        "Library": "backgrounds.w07",
        "Management": "backgrounds.w08",
        "My Learning": "backgrounds.w09",
    }
    for module_id, background_token in module_backgrounds.items():
        registry.register_module(
            ModuleThemeContract(module_id, background_token, shared)
        )
    return registry
