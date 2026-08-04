"""Public compatibility interface consumed by the Ultra Brain UI host."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Mapping, Protocol, runtime_checkable

from .adapter import ThemeAdapter
from .contracts import ComponentContract, ModuleThemeContract, ThemeContract
from .registry import (
    ThemeRegistry,
    UIRegistry,
    build_default_theme_registry,
    build_default_ui_registry,
)


@runtime_checkable
class UltraBrainUIInterface(Protocol):
    """Stable host-facing port; contains presentation concerns only."""

    def resolve_theme(
        self, settings: Mapping[str, Any] | None = None
    ) -> ThemeContract: ...

    def render_theme_css(
        self, settings: Mapping[str, Any] | None = None
    ) -> str: ...

    def component_contract(self, component_id: str) -> ComponentContract: ...

    def module_contract(self, module_id: str) -> ModuleThemeContract: ...


class UICompatibilityLayer:
    """Facade joining the versioned contract, adapter, and registries."""

    def __init__(
        self,
        theme_registry: ThemeRegistry | None = None,
        ui_registry: UIRegistry | None = None,
    ) -> None:
        self.theme_registry = theme_registry or build_default_theme_registry()
        self.ui_registry = ui_registry or build_default_ui_registry()
        self.adapter = ThemeAdapter(self.theme_registry.resolve("ule-official"))

    def resolve_theme(
        self, settings: Mapping[str, Any] | None = None
    ) -> ThemeContract:
        return self.adapter.adapt(settings)

    def render_theme_css(
        self, settings: Mapping[str, Any] | None = None
    ) -> str:
        return self.adapter.render_css(self.resolve_theme(settings))

    def component_contract(self, component_id: str) -> ComponentContract:
        return self.ui_registry.component(component_id)

    def module_contract(self, module_id: str) -> ModuleThemeContract:
        return self.ui_registry.module(module_id)


@lru_cache(maxsize=1)
def get_ui_compatibility_layer() -> UICompatibilityLayer:
    """Return the process-wide immutable UI compatibility facade."""

    return UICompatibilityLayer()
