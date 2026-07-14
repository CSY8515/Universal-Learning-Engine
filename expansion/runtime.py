"""Synchronous, in-process Pack Runtime and isolated Pack Sessions for v0.8."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .errors import (
    PackContractError,
    PackExecutionError,
    PackSessionNotFoundError,
    PackStateError,
)
from .interfaces import ExecutableExpansionPack, validate_pack
from .loader import PackLoader
from .registry import PackRegistry


@dataclass(frozen=True, slots=True)
class PackSession:
    """One exact pack's private, process-local execution state container."""

    session_id: str
    pack_id: str
    version: str
    state: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def identity(self) -> tuple[str, str]:
        return self.pack_id, self.version


@dataclass(frozen=True)
class PackSessionStatus:
    """Immutable public snapshot that never exposes pack-owned session state."""

    session_id: str
    pack_id: str
    version: str
    running: bool


class PackRuntime:
    """Coordinate one synchronous active session per exact loaded pack."""

    def __init__(self, registry: PackRegistry, loader: PackLoader) -> None:
        if not isinstance(registry, PackRegistry):
            raise TypeError("registry must be a PackRegistry")
        if not isinstance(loader, PackLoader):
            raise TypeError("loader must be a PackLoader")
        if loader.registry is not registry:
            raise ValueError("loader must use the supplied registry")
        self._registry = registry
        self._loader = loader
        self._sessions_by_identity: dict[tuple[str, str], PackSession] = {}
        self._sessions_by_id: dict[str, PackSession] = {}
        self._transitioning: set[tuple[str, str]] = set()

    @staticmethod
    def _required_session_id(session_id: object) -> str:
        if not isinstance(session_id, str) or not session_id.strip():
            raise PackContractError("session_id must be a non-empty string")
        return session_id.strip()

    @staticmethod
    def _status(session: PackSession, running: bool) -> PackSessionStatus:
        return PackSessionStatus(
            session_id=session.session_id,
            pack_id=session.pack_id,
            version=session.version,
            running=running,
        )

    def _new_session_id(self) -> str:
        session_id = uuid4().hex
        while session_id in self._sessions_by_id:
            session_id = uuid4().hex
        return session_id

    def start(
        self, pack_id: str, version: str | None = None
    ) -> PackSessionStatus:
        identity = self._registry.resolve_identity(pack_id, version)
        self._loader.require_loaded(*identity)
        if identity in self._sessions_by_identity or identity in self._transitioning:
            raise PackStateError(
                f"pack {identity[0]!r} version {identity[1]!r} is already running"
            )

        pack = self._registry.get(*identity)
        if not isinstance(pack, ExecutableExpansionPack):
            raise PackContractError("pack does not implement ExecutableExpansionPack")
        if validate_pack(pack) != self._registry.get_manifest(*identity):
            raise PackContractError("installed pack manifest changed")

        session = PackSession(self._new_session_id(), *identity)
        self._transitioning.add(identity)
        try:
            pack.execute(session)
        except Exception as error:
            try:
                pack.terminate(session)
            except Exception:
                pass
            raise PackExecutionError(
                f"pack {identity[0]!r} version {identity[1]!r} failed to execute"
            ) from error
        finally:
            self._transitioning.remove(identity)

        self._sessions_by_identity[identity] = session
        self._sessions_by_id[session.session_id] = session
        return self._status(session, True)

    def stop(self, session_id: str) -> PackSessionStatus:
        normalized_id = self._required_session_id(session_id)
        session = self._sessions_by_id.get(normalized_id)
        if session is None:
            raise PackSessionNotFoundError(
                f"pack session {normalized_id!r} is not active"
            )
        if session.identity in self._transitioning:
            raise PackStateError(
                f"pack {session.pack_id!r} version {session.version!r} "
                "is changing runtime state"
            )

        pack = self._registry.get(*session.identity)
        if not isinstance(pack, ExecutableExpansionPack):
            raise PackContractError("running pack lost its executable contract")
        self._transitioning.add(session.identity)
        try:
            pack.terminate(session)
        except Exception as error:
            raise PackExecutionError(
                f"pack {session.pack_id!r} version {session.version!r} "
                "failed to terminate"
            ) from error
        finally:
            self._transitioning.remove(session.identity)

        del self._sessions_by_id[normalized_id]
        del self._sessions_by_identity[session.identity]
        return self._status(session, False)

    def stop_pack(
        self, pack_id: str, version: str | None = None
    ) -> PackSessionStatus | None:
        identity = self._registry.resolve_identity(pack_id, version)
        session = self._sessions_by_identity.get(identity)
        if session is None:
            return None
        return self.stop(session.session_id)

    def get(self, session_id: str) -> PackSessionStatus:
        normalized_id = self._required_session_id(session_id)
        session = self._sessions_by_id.get(normalized_id)
        if session is None:
            raise PackSessionNotFoundError(
                f"pack session {normalized_id!r} is not active"
            )
        return self._status(session, True)

    def is_running(self, pack_id: str, version: str | None = None) -> bool:
        identity = self._registry.resolve_identity(pack_id, version)
        return identity in self._sessions_by_identity

    def sessions(self) -> tuple[PackSessionStatus, ...]:
        ordered = sorted(
            self._sessions_by_id.values(),
            key=lambda session: (
                session.pack_id,
                session.version,
                session.session_id,
            ),
        )
        return tuple(self._status(session, True) for session in ordered)
