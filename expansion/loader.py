"""Lifecycle loader for installed v0.7 Expansion Packs."""

from .errors import PackContractError, PackLoadError, PackStateError
from .interfaces import PackManifest, validate_pack
from .registry import PackRegistry


class PackLoader:
    """Load and unload exact pack versions from a Pack Registry."""

    def __init__(self, registry: PackRegistry) -> None:
        if not isinstance(registry, PackRegistry):
            raise TypeError("registry must be a PackRegistry")
        self._registry = registry
        self._loaded: set[tuple[str, str]] = set()

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

        try:
            pack.on_load()
        except Exception as error:
            raise PackLoadError(
                f"pack {identity[0]!r} version {identity[1]!r} failed to load"
            ) from error

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
        try:
            pack.on_unload()
        except Exception as error:
            raise PackLoadError(
                f"pack {identity[0]!r} version {identity[1]!r} failed to unload"
            ) from error

        self._loaded.remove(identity)
        return manifest

    def is_loaded(self, pack_id: str, version: str | None = None) -> bool:
        identity = self._registry.resolve_identity(pack_id, version)
        return identity in self._loaded

    def loaded_identities(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._loaded))
