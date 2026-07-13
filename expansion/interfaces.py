"""Common v0.7 Expansion Pack contracts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .errors import IncompatiblePackError, PackContractError


EXPANSION_INTERFACE_VERSION = "0.7"


def _required_text(field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PackContractError(f"{field_name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class PackManifest:
    """Immutable exact identity and compatibility information for one pack."""

    pack_id: str
    name: str
    version: str
    interface_version: str = EXPANSION_INTERFACE_VERSION

    def __post_init__(self) -> None:
        for field_name in ("pack_id", "name", "version", "interface_version"):
            object.__setattr__(
                self,
                field_name,
                _required_text(field_name, getattr(self, field_name)),
            )

    @property
    def identity(self) -> tuple[str, str]:
        return self.pack_id, self.version


class ExpansionPack(ABC):
    """Lifecycle-only common interface implemented by every v0.7 pack."""

    @property
    @abstractmethod
    def manifest(self) -> PackManifest:
        """Return this pack's immutable manifest."""

    @abstractmethod
    def on_load(self) -> None:
        """Activate this exact installed pack version."""

    @abstractmethod
    def on_unload(self) -> None:
        """Deactivate this exact loaded pack version."""


def validate_pack(pack: object) -> PackManifest:
    """Validate the common interface without invoking pack lifecycle code."""

    if not isinstance(pack, ExpansionPack):
        raise PackContractError("pack must implement ExpansionPack")

    manifest = pack.manifest
    if not isinstance(manifest, PackManifest):
        raise PackContractError("pack manifest must be a PackManifest")
    if manifest.interface_version != EXPANSION_INTERFACE_VERSION:
        raise IncompatiblePackError(
            "pack interface version must be " + EXPANSION_INTERFACE_VERSION
        )
    return manifest
