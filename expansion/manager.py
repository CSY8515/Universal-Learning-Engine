"""Stable Pack management and exact-version coordination."""

from dataclasses import dataclass

from .interfaces import ExpansionPack, PackManifest
from .loader import PackLoader
from .registry import PackRegistry
from .runtime import PackRuntime, PackSessionStatus


@dataclass(frozen=True)
class PackStatus:
    """Immutable public state for one exact installed pack version."""

    pack_id: str
    name: str
    version: str
    interface_version: str
    loaded: bool


class PackManager:
    """Coordinate install, lifecycle, removal, and version-aware lookup."""

    def __init__(self, registry: PackRegistry | None = None) -> None:
        self._registry = registry if registry is not None else PackRegistry()
        if not isinstance(self._registry, PackRegistry):
            raise TypeError("registry must be a PackRegistry")
        self._loader = PackLoader(self._registry)
        self._runtime = PackRuntime(self._registry, self._loader)

    def _status(self, manifest: PackManifest) -> PackStatus:
        return PackStatus(
            pack_id=manifest.pack_id,
            name=manifest.name,
            version=manifest.version,
            interface_version=manifest.interface_version,
            loaded=self._loader.is_loaded(manifest.pack_id, manifest.version),
        )

    def install(self, pack: ExpansionPack) -> PackStatus:
        manifest = self._registry.register(pack)
        return self._status(manifest)

    def remove(self, pack_id: str, version: str | None = None) -> PackManifest:
        identity = self._registry.resolve_identity(pack_id, version)
        self._runtime.stop_pack(*identity)
        if self._loader.is_loaded(*identity):
            self._loader.unload(*identity)
        return self._registry.unregister(*identity)

    def load(self, pack_id: str, version: str | None = None) -> PackStatus:
        manifest = self._loader.load(pack_id, version)
        return self._status(manifest)

    def unload(self, pack_id: str, version: str | None = None) -> PackStatus:
        identity = self._registry.resolve_identity(pack_id, version)
        self._runtime.stop_pack(*identity)
        manifest = self._loader.unload(*identity)
        return self._status(manifest)

    def start(
        self, pack_id: str, version: str | None = None
    ) -> PackSessionStatus:
        return self._runtime.start(pack_id, version)

    def stop(self, session_id: str) -> PackSessionStatus:
        return self._runtime.stop(session_id)

    def session(self, session_id: str) -> PackSessionStatus:
        return self._runtime.get(session_id)

    def sessions(self) -> tuple[PackSessionStatus, ...]:
        return self._runtime.sessions()

    def get(self, pack_id: str, version: str | None = None) -> PackStatus:
        manifest = self._registry.get_manifest(pack_id, version)
        return self._status(manifest)

    def list(self) -> tuple[PackStatus, ...]:
        return tuple(self._status(manifest) for manifest in self._registry.manifests())

    def versions(self, pack_id: str) -> tuple[str, ...]:
        return self._registry.versions(pack_id)
