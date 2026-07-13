"""In-process Pack Registry for v0.7."""

from collections.abc import Iterable

from .errors import (
    AmbiguousPackVersionError,
    DuplicatePackError,
    PackContractError,
    PackNotFoundError,
)
from .interfaces import ExpansionPack, PackManifest, validate_pack


class PackRegistry:
    """Store installed pack instances by exact ``(pack_id, version)`` identity."""

    def __init__(self) -> None:
        self._packs: dict[
            tuple[str, str], tuple[ExpansionPack, PackManifest]
        ] = {}

    @staticmethod
    def _required_identity_text(field_name: str, value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise PackContractError(f"{field_name} must be a non-empty string")
        return value.strip()

    def register(self, pack: ExpansionPack) -> PackManifest:
        manifest = validate_pack(pack)
        if manifest.identity in self._packs:
            raise DuplicatePackError(
                f"pack {manifest.pack_id!r} version {manifest.version!r} is installed"
            )
        self._packs[manifest.identity] = (pack, manifest)
        return manifest

    def resolve_identity(
        self, pack_id: str, version: str | None = None
    ) -> tuple[str, str]:
        normalized_id = self._required_identity_text("pack_id", pack_id)
        if version is not None:
            normalized_version = self._required_identity_text("version", version)
            identity = normalized_id, normalized_version
            if identity not in self._packs:
                raise PackNotFoundError(
                    f"pack {normalized_id!r} version {normalized_version!r} is not installed"
                )
            return identity

        matches = [key for key in self._packs if key[0] == normalized_id]
        if not matches:
            raise PackNotFoundError(f"pack {normalized_id!r} is not installed")
        if len(matches) > 1:
            raise AmbiguousPackVersionError(
                f"pack {normalized_id!r} has multiple installed versions"
            )
        return matches[0]

    def get(self, pack_id: str, version: str | None = None) -> ExpansionPack:
        return self._packs[self.resolve_identity(pack_id, version)][0]

    def get_manifest(
        self, pack_id: str, version: str | None = None
    ) -> PackManifest:
        return self._packs[self.resolve_identity(pack_id, version)][1]

    def unregister(self, pack_id: str, version: str | None = None) -> PackManifest:
        identity = self.resolve_identity(pack_id, version)
        _, manifest = self._packs.pop(identity)
        return manifest

    def contains(self, pack_id: str, version: str) -> bool:
        try:
            identity = self.resolve_identity(pack_id, version)
        except PackNotFoundError:
            return False
        return identity in self._packs

    def manifests(self) -> tuple[PackManifest, ...]:
        ordered = sorted(self._packs)
        return tuple(self._packs[identity][1] for identity in ordered)

    def versions(self, pack_id: str) -> tuple[str, ...]:
        normalized_id = self._required_identity_text("pack_id", pack_id)
        return tuple(sorted(key[1] for key in self._packs if key[0] == normalized_id))

    def __len__(self) -> int:
        return len(self._packs)

    def __iter__(self) -> Iterable[PackManifest]:
        return iter(self.manifests())
