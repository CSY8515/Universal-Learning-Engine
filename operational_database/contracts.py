"""Public contracts for the v1.08 operational database subsystem."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


OPERATIONAL_INTERFACE_VERSION = "1.0"
OPERATIONAL_SCHEMA_VERSION = 1


class RecordCategory(str, Enum):
    """Closed operational record classification required by v1.08."""

    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    WARNING = "warning"
    INCIDENT = "incident"
    RECOVERY = "recovery"
    ROLLBACK = "rollback"
    VALIDATION_FAILURE = "validation_failure"
    EXECUTION_FAILURE = "execution_failure"
    INVALID_DATA = "invalid_data"
    REJECTED_DECISION = "rejected_decision"
    UNRESOLVED_ISSUE = "unresolved_issue"


class RecordSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecordStatus(str, Enum):
    OBSERVED = "observed"
    OPEN = "open"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class RecordTypeDefinition:
    category: RecordCategory
    default_severity: RecordSeverity
    description: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ManagerCapabilityDefinition:
    name: str
    description: str


@dataclass(frozen=True)
class OperationalRecordInput:
    category: RecordCategory
    source: str
    event_type: str
    message: str
    occurred_at: str
    severity: RecordSeverity
    status: RecordStatus
    correlation_id: str = ""
    operation_id: str = ""
    entity_id: str = ""
    outcome: str = ""
    payload: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)
    record_id: str = ""


@dataclass(frozen=True)
class OperationalRecord:
    record_id: str
    category: RecordCategory
    source: str
    event_type: str
    message: str
    occurred_at: str
    observed_at: str
    severity: RecordSeverity
    status: RecordStatus
    correlation_id: str
    operation_id: str
    entity_id: str
    outcome: str
    payload: Mapping[str, object]
    metadata: Mapping[str, object]
    fingerprint: str
    duplicate_of: str = ""
    schema_version: int = OPERATIONAL_SCHEMA_VERSION


@dataclass(frozen=True)
class OperationalQuery:
    categories: tuple[RecordCategory, ...] = ()
    sources: tuple[str, ...] = ()
    correlation_id: str = ""
    occurred_after: str = ""
    occurred_before: str = ""
    include_duplicates: bool = True
    limit: int = 500


class OperationalDataPlane(ABC):
    """Storage contract; implementations may not silently delete records."""

    @abstractmethod
    def initialize(self) -> None:
        """Create or verify the versioned data-plane structure."""

    @abstractmethod
    def synchronize_registry(
        self, definitions: tuple[RecordTypeDefinition, ...]
    ) -> None:
        """Persist the active record-type registry without record mutation."""

    @abstractmethod
    def append(self, record: OperationalRecord) -> OperationalRecord:
        """Atomically append one immutable operational record."""

    @abstractmethod
    def get(self, record_id: str) -> OperationalRecord | None:
        """Return one record without exposing mutable storage state."""

    @abstractmethod
    def query(self, query: OperationalQuery) -> tuple[OperationalRecord, ...]:
        """Return a deterministic bounded record view."""

    @abstractmethod
    def find_canonical_by_fingerprint(
        self, fingerprint: str
    ) -> OperationalRecord | None:
        """Return the first non-duplicate record for one fingerprint."""

    @abstractmethod
    def count(self, *, include_duplicates: bool = True) -> int:
        """Count retained records."""

    @abstractmethod
    def save_report(self, report_id: str, generated_at: str, payload: str) -> None:
        """Atomically retain a generated operational report snapshot."""

    @abstractmethod
    def latest_report(self) -> str | None:
        """Return the latest stored report payload, when present."""

    @abstractmethod
    def close(self) -> None:
        """Release data-plane resources."""


class OperationalReportSink(ABC):
    """Upper-layer reporting boundary implemented by integrations."""

    @abstractmethod
    def publish_operational_report(self, report: Mapping[str, object]) -> object:
        """Publish one summary report without raw record payloads."""
