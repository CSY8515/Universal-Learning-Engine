"""Stable facade over the v1.08 operational database data plane."""

from __future__ import annotations

from pathlib import Path

from .contracts import OperationalDataPlane, OperationalQuery, OperationalRecord
from .data_plane import SQLiteOperationalDataPlane
from .errors import OperationalContractError
from .registry import OperationalRecordRegistry, default_record_registry


DEFAULT_OPERATIONAL_DATABASE_PATH = Path(".ule_data") / "operational.db"


class OperationalDatabase:
    """Coordinate Registry and Data Plane without changing application runtime."""

    def __init__(
        self,
        path: str | Path | None = None,
        *,
        registry: OperationalRecordRegistry | None = None,
        data_plane: OperationalDataPlane | None = None,
    ) -> None:
        if path is not None and data_plane is not None:
            raise OperationalContractError(
                "path and data_plane cannot be supplied together"
            )
        self._registry = registry if registry is not None else default_record_registry()
        if not isinstance(self._registry, OperationalRecordRegistry):
            raise OperationalContractError(
                "registry must be an OperationalRecordRegistry"
            )
        self._data_plane = (
            data_plane
            if data_plane is not None
            else SQLiteOperationalDataPlane(path or DEFAULT_OPERATIONAL_DATABASE_PATH)
        )
        if not isinstance(self._data_plane, OperationalDataPlane):
            raise OperationalContractError(
                "data_plane must implement OperationalDataPlane"
            )
        self._data_plane.initialize()
        self._data_plane.synchronize_registry(self._registry.definitions())

    @property
    def registry(self) -> OperationalRecordRegistry:
        return self._registry

    @property
    def data_plane(self) -> OperationalDataPlane:
        return self._data_plane

    def append(self, record: OperationalRecord) -> OperationalRecord:
        self._registry.resolve(record.category)
        return self._data_plane.append(record)

    def get(self, record_id: str) -> OperationalRecord | None:
        return self._data_plane.get(record_id)

    def query(
        self, query: OperationalQuery | None = None
    ) -> tuple[OperationalRecord, ...]:
        return self._data_plane.query(query or OperationalQuery())

    def find_canonical_by_fingerprint(
        self, fingerprint: str
    ) -> OperationalRecord | None:
        return self._data_plane.find_canonical_by_fingerprint(fingerprint)

    def count(self, *, include_duplicates: bool = True) -> int:
        return self._data_plane.count(include_duplicates=include_duplicates)

    def save_report(self, report_id: str, generated_at: str, payload: str) -> None:
        self._data_plane.save_report(report_id, generated_at, payload)

    def latest_report(self) -> str | None:
        return self._data_plane.latest_report()

    def close(self) -> None:
        self._data_plane.close()

    def __enter__(self) -> "OperationalDatabase":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()
