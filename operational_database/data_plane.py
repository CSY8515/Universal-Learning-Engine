"""SQLite implementation of the append-only v1.08 operational data plane."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

from .contracts import (
    OPERATIONAL_SCHEMA_VERSION,
    OperationalDataPlane,
    OperationalQuery,
    OperationalRecord,
    RecordCategory,
    RecordSeverity,
    RecordStatus,
    RecordTypeDefinition,
)
from .errors import OperationalContractError, OperationalStorageError


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_mapping(value: str) -> dict[str, object]:
    try:
        payload = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise OperationalStorageError("stored operational JSON is invalid") from exc
    if not isinstance(payload, dict):
        raise OperationalStorageError("stored operational JSON must be an object")
    return payload


class SQLiteOperationalDataPlane(OperationalDataPlane):
    """Versioned SQLite storage with no public record-deletion operation."""

    def __init__(self, path: str | Path) -> None:
        self._path = str(path)
        if not self._path.strip():
            raise OperationalContractError("database path must not be empty")
        self._connection: sqlite3.Connection | None = None
        self._lock = threading.RLock()

    @property
    def path(self) -> str:
        return self._path

    def _connection_or_raise(self) -> sqlite3.Connection:
        if self._connection is None:
            raise OperationalStorageError("data plane is not initialized")
        return self._connection

    def initialize(self) -> None:
        with self._lock:
            if self._connection is not None:
                return
            if self._path != ":memory:":
                Path(self._path).expanduser().parent.mkdir(parents=True, exist_ok=True)
            try:
                connection = sqlite3.connect(self._path, check_same_thread=False)
                connection.row_factory = sqlite3.Row
                connection.execute("PRAGMA foreign_keys = ON")
                if self._path != ":memory:":
                    connection.execute("PRAGMA journal_mode = WAL")
                self._connection = connection
                self._initialize_schema(connection)
            except sqlite3.Error as exc:
                if self._connection is not None:
                    self._connection.close()
                    self._connection = None
                raise OperationalStorageError(
                    "operational data plane initialization failed"
                ) from exc

    def _initialize_schema(self, connection: sqlite3.Connection) -> None:
        with connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS operational_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS operational_record_types (
                    category TEXT PRIMARY KEY,
                    default_severity TEXT NOT NULL,
                    description TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS operational_records (
                    record_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    source TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    operation_id TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    duplicate_of TEXT,
                    schema_version INTEGER NOT NULL,
                    FOREIGN KEY(category) REFERENCES operational_record_types(category),
                    FOREIGN KEY(duplicate_of) REFERENCES operational_records(record_id)
                );

                CREATE INDEX IF NOT EXISTS idx_operational_records_category
                    ON operational_records(category, occurred_at, record_id);
                CREATE INDEX IF NOT EXISTS idx_operational_records_source
                    ON operational_records(source, occurred_at, record_id);
                CREATE INDEX IF NOT EXISTS idx_operational_records_correlation
                    ON operational_records(correlation_id, occurred_at, record_id);
                CREATE INDEX IF NOT EXISTS idx_operational_records_fingerprint
                    ON operational_records(fingerprint, duplicate_of);

                CREATE TABLE IF NOT EXISTS operational_reports (
                    report_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    schema_version INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_operational_reports_generated
                    ON operational_reports(generated_at, report_id);
                """
            )
            row = connection.execute(
                "SELECT value FROM operational_metadata WHERE key = 'schema_version'"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO operational_metadata(key, value) VALUES (?, ?)",
                    ("schema_version", str(OPERATIONAL_SCHEMA_VERSION)),
                )
            elif row["value"] != str(OPERATIONAL_SCHEMA_VERSION):
                raise OperationalStorageError(
                    "unsupported operational database schema version"
                )

    def synchronize_registry(
        self, definitions: tuple[RecordTypeDefinition, ...]
    ) -> None:
        connection = self._connection_or_raise()
        with self._lock, connection:
            for definition in definitions:
                connection.execute(
                    """
                    INSERT INTO operational_record_types(
                        category, default_severity, description
                    ) VALUES (?, ?, ?)
                    ON CONFLICT(category) DO UPDATE SET
                        default_severity = excluded.default_severity,
                        description = excluded.description
                    """,
                    (
                        definition.category.value,
                        definition.default_severity.value,
                        definition.description,
                    ),
                )

    def append(self, record: OperationalRecord) -> OperationalRecord:
        if not isinstance(record, OperationalRecord):
            raise OperationalContractError("record must be an OperationalRecord")
        connection = self._connection_or_raise()
        try:
            with self._lock, connection:
                connection.execute(
                    """
                    INSERT INTO operational_records(
                        record_id, category, source, event_type, message,
                        occurred_at, observed_at, severity, status,
                        correlation_id, operation_id, entity_id, outcome,
                        payload_json, metadata_json, fingerprint, duplicate_of,
                        schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.record_id,
                        record.category.value,
                        record.source,
                        record.event_type,
                        record.message,
                        record.occurred_at,
                        record.observed_at,
                        record.severity.value,
                        record.status.value,
                        record.correlation_id,
                        record.operation_id,
                        record.entity_id,
                        record.outcome,
                        _json_text(dict(record.payload)),
                        _json_text(dict(record.metadata)),
                        record.fingerprint,
                        record.duplicate_of or None,
                        record.schema_version,
                    ),
                )
        except (sqlite3.Error, TypeError, ValueError) as exc:
            raise OperationalStorageError("operational record append failed") from exc
        return record

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> OperationalRecord:
        return OperationalRecord(
            record_id=row["record_id"],
            category=RecordCategory(row["category"]),
            source=row["source"],
            event_type=row["event_type"],
            message=row["message"],
            occurred_at=row["occurred_at"],
            observed_at=row["observed_at"],
            severity=RecordSeverity(row["severity"]),
            status=RecordStatus(row["status"]),
            correlation_id=row["correlation_id"],
            operation_id=row["operation_id"],
            entity_id=row["entity_id"],
            outcome=row["outcome"],
            payload=_json_mapping(row["payload_json"]),
            metadata=_json_mapping(row["metadata_json"]),
            fingerprint=row["fingerprint"],
            duplicate_of=row["duplicate_of"] or "",
            schema_version=int(row["schema_version"]),
        )

    def get(self, record_id: str) -> OperationalRecord | None:
        if not isinstance(record_id, str) or not record_id.strip():
            raise OperationalContractError("record_id must be a non-empty string")
        connection = self._connection_or_raise()
        with self._lock:
            row = connection.execute(
                "SELECT * FROM operational_records WHERE record_id = ?",
                (record_id.strip(),),
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def query(self, query: OperationalQuery) -> tuple[OperationalRecord, ...]:
        if not isinstance(query, OperationalQuery):
            raise OperationalContractError("query must be an OperationalQuery")
        if isinstance(query.limit, bool) or not 1 <= query.limit <= 10000:
            raise OperationalContractError("query limit must be from 1 through 10000")
        clauses: list[str] = []
        parameters: list[object] = []
        if query.categories:
            clauses.append(
                "category IN (" + ",".join("?" for _ in query.categories) + ")"
            )
            parameters.extend(category.value for category in query.categories)
        if query.sources:
            clauses.append("source IN (" + ",".join("?" for _ in query.sources) + ")")
            parameters.extend(query.sources)
        if query.correlation_id:
            clauses.append("correlation_id = ?")
            parameters.append(query.correlation_id)
        if query.occurred_after:
            clauses.append("occurred_at >= ?")
            parameters.append(query.occurred_after)
        if query.occurred_before:
            clauses.append("occurred_at <= ?")
            parameters.append(query.occurred_before)
        if not query.include_duplicates:
            clauses.append("duplicate_of IS NULL")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        parameters.append(query.limit)
        connection = self._connection_or_raise()
        with self._lock:
            rows = connection.execute(
                "SELECT * FROM operational_records"
                + where
                + " ORDER BY occurred_at, observed_at, record_id LIMIT ?",
                tuple(parameters),
            ).fetchall()
        return tuple(self._row_to_record(row) for row in rows)

    def find_canonical_by_fingerprint(
        self, fingerprint: str
    ) -> OperationalRecord | None:
        if not isinstance(fingerprint, str) or not fingerprint.strip():
            raise OperationalContractError("fingerprint must be a non-empty string")
        connection = self._connection_or_raise()
        with self._lock:
            row = connection.execute(
                """
                SELECT * FROM operational_records
                WHERE fingerprint = ? AND duplicate_of IS NULL
                ORDER BY occurred_at, observed_at, record_id LIMIT 1
                """,
                (fingerprint.strip(),),
            ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def count(self, *, include_duplicates: bool = True) -> int:
        connection = self._connection_or_raise()
        where = "" if include_duplicates else " WHERE duplicate_of IS NULL"
        with self._lock:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM operational_records" + where
            ).fetchone()
        return int(row["count"])

    def save_report(self, report_id: str, generated_at: str, payload: str) -> None:
        if not all(isinstance(value, str) and value.strip() for value in (report_id, generated_at, payload)):
            raise OperationalContractError("report fields must be non-empty strings")
        connection = self._connection_or_raise()
        try:
            with self._lock, connection:
                connection.execute(
                    """
                    INSERT INTO operational_reports(
                        report_id, generated_at, payload_json, schema_version
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (report_id, generated_at, payload, OPERATIONAL_SCHEMA_VERSION),
                )
        except sqlite3.Error as exc:
            raise OperationalStorageError("operational report storage failed") from exc

    def latest_report(self) -> str | None:
        connection = self._connection_or_raise()
        with self._lock:
            row = connection.execute(
                """
                SELECT payload_json FROM operational_reports
                ORDER BY generated_at DESC, report_id DESC LIMIT 1
                """
            ).fetchone()
        return row["payload_json"] if row is not None else None

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
