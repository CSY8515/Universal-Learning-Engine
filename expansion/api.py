"""Public facade for the v0.7 Expansion Platform."""

from .interfaces import ExpansionPack, PackManifest
from .manager import PackManager, PackStatus


class ExpansionAPI:
    """Expose only the approved v0.7 pack-management operations."""

    def __init__(self, manager: PackManager | None = None) -> None:
        self._manager = manager if manager is not None else PackManager()
        if not isinstance(self._manager, PackManager):
            raise TypeError("manager must be a PackManager")

    def install(self, pack: ExpansionPack) -> PackStatus:
        return self._manager.install(pack)

    def remove(self, pack_id: str, version: str | None = None) -> PackManifest:
        return self._manager.remove(pack_id, version)

    def load(self, pack_id: str, version: str | None = None) -> PackStatus:
        return self._manager.load(pack_id, version)

    def unload(self, pack_id: str, version: str | None = None) -> PackStatus:
        return self._manager.unload(pack_id, version)

    def get(self, pack_id: str, version: str | None = None) -> PackStatus:
        return self._manager.get(pack_id, version)

    def list(self) -> tuple[PackStatus, ...]:
        return self._manager.list()

    def versions(self, pack_id: str) -> tuple[str, ...]:
        return self._manager.versions(pack_id)
