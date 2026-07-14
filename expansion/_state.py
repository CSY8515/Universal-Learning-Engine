"""Internal cross-layer state guard for Pack Loader and Runtime transitions."""

from .errors import PackStateError


class PackStateCoordinator:
    """Reject conflicting lifecycle/runtime transitions without owning state."""

    def __init__(self) -> None:
        self._lifecycle_transitions: set[tuple[str, str]] = set()
        self._runtime_transitions: set[tuple[str, str]] = set()
        self._active_runtime_identities: set[tuple[str, str]] = set()

    @staticmethod
    def _description(identity: tuple[str, str]) -> str:
        return f"pack {identity[0]!r} version {identity[1]!r}"

    def begin_lifecycle(self, identity: tuple[str, str]) -> None:
        if (
            identity in self._lifecycle_transitions
            or identity in self._runtime_transitions
            or identity in self._active_runtime_identities
        ):
            raise PackStateError(
                f"{self._description(identity)} cannot change lifecycle state "
                "during an active runtime state"
            )
        self._lifecycle_transitions.add(identity)

    def end_lifecycle(self, identity: tuple[str, str]) -> None:
        self._lifecycle_transitions.discard(identity)

    def begin_start(self, identity: tuple[str, str]) -> None:
        if (
            identity in self._lifecycle_transitions
            or identity in self._runtime_transitions
            or identity in self._active_runtime_identities
        ):
            raise PackStateError(
                f"{self._description(identity)} cannot start in its current state"
            )
        self._runtime_transitions.add(identity)

    def begin_stop(self, identity: tuple[str, str]) -> None:
        if identity in self._lifecycle_transitions or identity in self._runtime_transitions:
            raise PackStateError(
                f"{self._description(identity)} is changing runtime state"
            )
        self._runtime_transitions.add(identity)

    def end_runtime(self, identity: tuple[str, str]) -> None:
        self._runtime_transitions.discard(identity)

    def mark_active(self, identity: tuple[str, str]) -> None:
        self._active_runtime_identities.add(identity)

    def mark_inactive(self, identity: tuple[str, str]) -> None:
        self._active_runtime_identities.discard(identity)

