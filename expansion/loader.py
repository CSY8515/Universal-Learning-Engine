"""Lifecycle loader for installed Expansion Packs."""

import logging

from .errors import PackContractError, PackLoadError, PackStateError
from .interfaces import PackManifest, validate_pack
from .registry import PackRegistry
from ._state import PackStateCoordinator


LOGGER = logging.getLogger("universal_learning_engine.expansion")


class PackLoader:
    """Load and unload exact pack versions from a Pack Registry."""

    def __init__(self, registry: PackRegistry) -> None:
        if not isinstance(registry, PackRegistry):
            raise TypeError("registry must be a PackRegistry")
        self._registry = registry
        self._loaded: set[tuple[str, str]] = set()
        self._state = PackStateCoordinator()

    @property
    def registry(self) -> PackRegistry:
        """Return the Registry whose exact identities this Loader owns."""
        return self._registry

    def load(self, pack_id: str, version: str | None = None) -> PackManifest:
        identity = self._registry.resolve_identity(pack_id, version)
        if identity in self._loaded:
            raise PackStateError(
                f"pack {identity[0]!r} version {identity[1]!r} is already loaded"
            )

        pack = self._registry.get(*identity)
        manifest = validate_pack(pack)
        registered_manifest = self._registry.get_manifest(*identity)
        if manifest != registered_manifest:
            raise PackContractError("installed pack manifest changed")

        self._state.begin_lifecycle(identity)
        try:
            pack.on_load()
        except Exception as error:
            LOGGER.warning(
                "pack_lifecycle_failed operation=load pack_id=%s version=%s error_type=%s",
                identity[0], identity[1], type(error).__name__,
            )
            raise PackLoadError(
                f"pack {identity[0]!r} version {identity[1]!r} failed to load",
                operation="load", pack_id=identity[0], version=identity[1],
            ) from error
        finally:
            self._state.end_lifecycle(identity)

        self._loaded.add(identity)
        return registered_manifest

    def unload(self, pack_id: str, version: str | None = None) -> PackManifest:
        identity = self._registry.resolve_identity(pack_id, version)
        if identity not in self._loaded:
            raise PackStateError(
                f"pack {identity[0]!r} version {identity[1]!r} is not loaded"
            )

        pack = self._registry.get(*identity)
        manifest = self._registry.get_manifest(*identity)
        self._state.begin_lifecycle(identity)
        try:
            pack.on_unload()
        except Exception as error:
            LOGGER.warning(
                "pack_lifecycle_failed operation=unload pack_id=%s version=%s error_type=%s",
                identity[0], identity[1], type(error).__name__,
            )
            raise PackLoadError(
                f"pack {identity[0]!r} version {identity[1]!r} failed to unload",
                operation="unload", pack_id=identity[0], version=identity[1],
            ) from error
        finally:
            self._state.end_lifecycle(identity)

        self._loaded.remove(identity)
        return manifest

    def is_loaded(self, pack_id: str, version: str | None = None) -> bool:
        identity = self._registry.resolve_identity(pack_id, version)
        return identity in self._loaded

    def require_loaded(
        self, pack_id: str, version: str | None = None
    ) -> PackManifest:
        """Return the exact manifest or reject execution of an unloaded pack."""
        identity = self._registry.resolve_identity(pack_id, version)
        if identity not in self._loaded:
            raise PackStateError(
                f"pack {identity[0]!r} version {identity[1]!r} is not loaded"
            )
        return self._registry.get_manifest(*identity)

    def loaded_identities(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._loaded))
