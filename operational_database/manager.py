"""Database Manager validation, analysis, candidates, and reporting."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone

from .contracts import (
    OperationalQuery,
    OperationalRecord,
    OperationalRecordInput,
    OperationalReportSink,
    RecordCategory,
    RecordSeverity,
    RecordStatus,
    RecordTypeDefinition,
)
from .database import OperationalDatabase
from .errors import OperationalContractError, OperationalValidationError
from .registry import (
    DatabaseManagerRegistry,
    default_manager_registry,
)
from .reporting import (
    OperationalCandidate,
    OperationalPattern,
    OperationalRecommendation,
    OperationalReport,
)


_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
}
_OPEN_CATEGORIES = {
    RecordCategory.FAILURE,
    RecordCategory.ERROR,
    RecordCategory.INCIDENT,
    RecordCategory.VALIDATION_FAILURE,
    RecordCategory.EXECUTION_FAILURE,
    RecordCategory.INVALID_DATA,
    RecordCategory.UNRESOLVED_ISSUE,
}
_RESOLUTION_CATEGORIES = {RecordCategory.RECOVERY, RecordCategory.ROLLBACK}
_RULE_CATEGORIES = _OPEN_CATEGORIES | {RecordCategory.REJECTED_DECISION}
_STANDARD_CATEGORIES = {
    RecordCategory.SUCCESS,
    RecordCategory.RECOVERY,
    RecordCategory.ROLLBACK,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(field_name: str, value: object, maximum: int, *, required: bool) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise OperationalValidationError(f"{field_name} must be text")
    cleaned = value.strip()
    if required and not cleaned:
        raise OperationalValidationError(f"{field_name} must not be empty")
    if len(cleaned) > maximum:
        raise OperationalValidationError(
            f"{field_name} must not exceed {maximum} characters"
        )
    return cleaned


def _timestamp(field_name: str, value: object) -> str:
    text = _text(field_name, value, 64, required=True)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OperationalValidationError(
            f"{field_name} must be an ISO 8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds")


def _safe_json(value: object, *, field_name: str, key: str = "") -> object:
    if key.casefold() in _SENSITIVE_KEYS:
        return "[REDACTED]"
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise OperationalValidationError(f"{field_name} contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        result: dict[str, object] = {}
        for item_key, item_value in value.items():
            if not isinstance(item_key, str) or not item_key.strip():
                raise OperationalValidationError(
                    f"{field_name} keys must be non-empty strings"
                )
            cleaned_key = item_key.strip()
            result[cleaned_key] = _safe_json(
                item_value, field_name=field_name, key=cleaned_key
            )
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_safe_json(item, field_name=field_name) for item in value]
    raise OperationalValidationError(f"{field_name} must contain JSON-compatible data")


class DatabaseManager:
    """Own deterministic operational processing above the Database facade."""

    def __init__(
        self,
        database: OperationalDatabase,
        *,
        registry: DatabaseManagerRegistry | None = None,
    ) -> None:
        if not isinstance(database, OperationalDatabase):
            raise OperationalContractError("database must be an OperationalDatabase")
        self._database = database
        self._registry = registry if registry is not None else default_manager_registry()
        if not isinstance(self._registry, DatabaseManagerRegistry):
            raise OperationalContractError(
                "registry must be a DatabaseManagerRegistry"
            )

    @property
    def database(self) -> OperationalDatabase:
        return self._database

    @property
    def registry(self) -> DatabaseManagerRegistry:
        return self._registry

    def classify(self, value: RecordCategory | str) -> RecordTypeDefinition:
        """Resolve an explicit category through the Database Registry."""
        return self._database.registry.resolve(value)

    @staticmethod
    def _default_status(category: RecordCategory) -> RecordStatus:
        if category in _RESOLUTION_CATEGORIES:
            return RecordStatus.RESOLVED
        if category in _OPEN_CATEGORIES:
            return RecordStatus.OPEN
        return RecordStatus.OBSERVED

    def validate(self, raw: Mapping[str, object]) -> OperationalRecordInput:
        """Validate and sanitize untrusted operational input."""
        if not isinstance(raw, Mapping):
            raise OperationalValidationError("record input must be a mapping")
        definition = self.classify(raw.get("category", ""))
        severity_value = raw.get("severity", definition.default_severity.value)
        status_value = raw.get("status", self._default_status(definition.category).value)
        try:
            severity = (
                severity_value
                if isinstance(severity_value, RecordSeverity)
                else RecordSeverity(str(severity_value).strip().casefold())
            )
            status = (
                status_value
                if isinstance(status_value, RecordStatus)
                else RecordStatus(str(status_value).strip().casefold())
            )
        except ValueError as exc:
            raise OperationalValidationError("severity or status is unsupported") from exc
        occurred_at = _timestamp("occurred_at", raw.get("occurred_at") or _now())
        payload = _safe_json(raw.get("payload", {}), field_name="payload")
        metadata = _safe_json(raw.get("metadata", {}), field_name="metadata")
        if not isinstance(payload, dict) or not isinstance(metadata, dict):
            raise OperationalValidationError("payload and metadata must be mappings")
        return OperationalRecordInput(
            category=definition.category,
            source=_text("source", raw.get("source"), 160, required=True),
            event_type=_text("event_type", raw.get("event_type"), 160, required=True),
            message=_text("message", raw.get("message"), 2000, required=True),
            occurred_at=occurred_at,
            severity=severity,
            status=status,
            correlation_id=_text("correlation_id", raw.get("correlation_id"), 160, required=False),
            operation_id=_text("operation_id", raw.get("operation_id"), 160, required=False),
            entity_id=_text("entity_id", raw.get("entity_id"), 160, required=False),
            outcome=_text("outcome", raw.get("outcome"), 400, required=False),
            payload=payload,
            metadata=metadata,
            record_id=_text("record_id", raw.get("record_id"), 160, required=False),
        )

    @staticmethod
    def _fingerprint(value: OperationalRecordInput) -> str:
        identity = {
            "category": value.category.value,
            "source": value.source,
            "event_type": value.event_type,
            "message": value.message,
            "occurred_at": value.occurred_at,
            "correlation_id": value.correlation_id,
            "operation_id": value.operation_id,
            "entity_id": value.entity_id,
            "outcome": value.outcome,
            "payload": dict(value.payload),
        }
        encoded = json.dumps(
            identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def ingest(self, raw: Mapping[str, object]) -> OperationalRecord:
        """Validate, classify, non-destructively deduplicate, and append."""
        value = self.validate(raw)
        fingerprint = self._fingerprint(value)
        canonical = self._database.find_canonical_by_fingerprint(fingerprint)
        record = OperationalRecord(
            record_id=value.record_id or f"op_{uuid.uuid4().hex}",
            category=value.category,
            source=value.source,
            event_type=value.event_type,
            message=value.message,
            occurred_at=value.occurred_at,
            observed_at=_now(),
            severity=value.severity,
            status=value.status,
            correlation_id=value.correlation_id,
            operation_id=value.operation_id,
            entity_id=value.entity_id,
            outcome=value.outcome,
            payload=dict(value.payload),
            metadata=dict(value.metadata),
            fingerprint=fingerprint,
            duplicate_of=canonical.record_id if canonical is not None else "",
        )
        return self._database.append(record)

    def _records(self) -> tuple[OperationalRecord, ...]:
        return self._database.query(OperationalQuery(limit=10000))

    @staticmethod
    def _canonical(
        records: tuple[OperationalRecord, ...]
    ) -> tuple[OperationalRecord, ...]:
        return tuple(record for record in records if not record.duplicate_of)

    def analyze_patterns(
        self, records: tuple[OperationalRecord, ...] | None = None
    ) -> tuple[OperationalPattern, ...]:
        canonical = self._canonical(records if records is not None else self._records())
        counts = Counter(
            (record.category.value, record.source, record.event_type)
            for record in canonical
        )
        patterns = [
            OperationalPattern(
                code="repeated_operational_pattern",
                category=category,
                source=source,
                event_type=event_type,
                count=count,
                summary=f"{source}/{event_type} produced {category} {count} times.",
            )
            for (category, source, event_type), count in counts.items()
            if count >= 2
        ]
        return tuple(
            sorted(patterns, key=lambda item: (-item.count, item.category, item.source, item.event_type))
        )

    @staticmethod
    def _unresolved(
        records: tuple[OperationalRecord, ...]
    ) -> tuple[OperationalRecord, ...]:
        canonical = tuple(record for record in records if not record.duplicate_of)
        resolved_correlations = {
            record.correlation_id
            for record in canonical
            if record.category in _RESOLUTION_CATEGORIES and record.correlation_id
        }
        return tuple(
            record
            for record in canonical
            if record.category in _OPEN_CATEGORIES
            and record.status != RecordStatus.RESOLVED
            and (
                not record.correlation_id
                or record.correlation_id not in resolved_correlations
            )
        )

    def operational_analysis(
        self, records: tuple[OperationalRecord, ...] | None = None
    ) -> dict[str, object]:
        retained = records if records is not None else self._records()
        canonical = self._canonical(retained)
        category_counts = Counter(record.category.value for record in canonical)
        for category in RecordCategory:
            category_counts.setdefault(category.value, 0)
        return {
            "total_records": len(retained),
            "unique_records": len(canonical),
            "duplicate_records": len(retained) - len(canonical),
            "category_counts": dict(sorted(category_counts.items())),
            "severity_counts": dict(sorted(Counter(record.severity.value for record in canonical).items())),
            "status_counts": dict(sorted(Counter(record.status.value for record in canonical).items())),
            "source_counts": dict(sorted(Counter(record.source for record in canonical).items())),
            "unresolved_record_ids": tuple(record.record_id for record in self._unresolved(retained)),
        }

    def recommendations(
        self, records: tuple[OperationalRecord, ...] | None = None
    ) -> tuple[OperationalRecommendation, ...]:
        retained = records if records is not None else self._records()
        analysis = self.operational_analysis(retained)
        counts = analysis["category_counts"]
        results: list[OperationalRecommendation] = []
        unresolved_count = len(analysis["unresolved_record_ids"])
        if unresolved_count:
            results.append(OperationalRecommendation(
                "resolve_open_operations", "high",
                f"{unresolved_count} canonical operational records remain unresolved.",
                "Review each correlation and record an explicit Recovery or Rollback outcome.",
            ))
        validation_count = counts[RecordCategory.VALIDATION_FAILURE.value] + counts[RecordCategory.INVALID_DATA.value]
        if validation_count:
            results.append(OperationalRecommendation(
                "strengthen_validation_boundary", "medium",
                f"{validation_count} validation or invalid-data events were retained.",
                "Review the affected input contract before promoting any rule candidate.",
            ))
        execution_count = sum(counts[item.value] for item in (
            RecordCategory.FAILURE, RecordCategory.ERROR,
            RecordCategory.INCIDENT, RecordCategory.EXECUTION_FAILURE,
        ))
        if execution_count:
            results.append(OperationalRecommendation(
                "review_execution_recovery", "high",
                f"{execution_count} execution-impacting events were retained.",
                "Verify Recovery and Rollback evidence for the affected operations.",
            ))
        if analysis["duplicate_records"]:
            results.append(OperationalRecommendation(
                "review_duplicate_producers", "low",
                f"{analysis['duplicate_records']} duplicate observations were preserved.",
                "Review producer idempotency; canonical analysis already excludes duplicates.",
            ))
        return tuple(results)

    @staticmethod
    def _candidate_id(kind: str, pattern: OperationalPattern) -> str:
        value = f"{kind}|{pattern.category}|{pattern.source}|{pattern.event_type}"
        return f"candidate_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:20]}"

    def rule_candidates(
        self, patterns: tuple[OperationalPattern, ...]
    ) -> tuple[OperationalCandidate, ...]:
        return tuple(
            OperationalCandidate(
                candidate_id=self._candidate_id("rule", pattern),
                kind="rule",
                status="candidate",
                evidence_count=pattern.count,
                proposal=f"Evaluate a guard rule for {pattern.source}/{pattern.event_type}.",
                evidence={"category": pattern.category, "source": pattern.source, "event_type": pattern.event_type},
            )
            for pattern in patterns
            if pattern.count >= 3 and RecordCategory(pattern.category) in _RULE_CATEGORIES
        )

    def standard_candidates(
        self, patterns: tuple[OperationalPattern, ...]
    ) -> tuple[OperationalCandidate, ...]:
        return tuple(
            OperationalCandidate(
                candidate_id=self._candidate_id("standard", pattern),
                kind="standard",
                status="candidate",
                evidence_count=pattern.count,
                proposal=f"Evaluate {pattern.source}/{pattern.event_type} as an operational standard.",
                evidence={"category": pattern.category, "source": pattern.source, "event_type": pattern.event_type},
            )
            for pattern in patterns
            if pattern.count >= 3 and RecordCategory(pattern.category) in _STANDARD_CATEGORIES
        )

    def generate_operational_report(
        self, *, publish_to: OperationalReportSink | None = None
    ) -> OperationalReport:
        records = self._records()
        analysis = self.operational_analysis(records)
        patterns = self.analyze_patterns(records)
        generated_at = _now()
        occurred = [record.occurred_at for record in records]
        report = OperationalReport(
            report_id=f"report_{uuid.uuid4().hex}",
            generated_at=generated_at,
            period_start=min(occurred) if occurred else generated_at,
            period_end=max(occurred) if occurred else generated_at,
            total_records=analysis["total_records"],
            unique_records=analysis["unique_records"],
            duplicate_records=analysis["duplicate_records"],
            category_counts=analysis["category_counts"],
            severity_counts=analysis["severity_counts"],
            status_counts=analysis["status_counts"],
            source_counts=analysis["source_counts"],
            patterns=patterns,
            recommendations=self.recommendations(records),
            rule_candidates=self.rule_candidates(patterns),
            standard_candidates=self.standard_candidates(patterns),
            unresolved_record_ids=analysis["unresolved_record_ids"],
        )
        payload = report.to_dict()
        self._database.save_report(
            report.report_id,
            report.generated_at,
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
        )
        if publish_to is not None:
            if not isinstance(publish_to, OperationalReportSink):
                raise OperationalContractError(
                    "publish_to must implement OperationalReportSink"
                )
            publish_to.publish_operational_report(payload)
        return report
