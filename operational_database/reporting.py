"""Immutable operational reporting values for Database Manager."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from typing import Mapping

from .contracts import OPERATIONAL_INTERFACE_VERSION, OPERATIONAL_SCHEMA_VERSION


@dataclass(frozen=True)
class OperationalPattern:
    code: str
    category: str
    source: str
    event_type: str
    count: int
    summary: str


@dataclass(frozen=True)
class OperationalRecommendation:
    code: str
    priority: str
    reason: str
    action: str


@dataclass(frozen=True)
class OperationalCandidate:
    candidate_id: str
    kind: str
    status: str
    evidence_count: int
    proposal: str
    evidence: Mapping[str, object]


@dataclass(frozen=True)
class OperationalReport:
    report_id: str
    generated_at: str
    period_start: str
    period_end: str
    total_records: int
    unique_records: int
    duplicate_records: int
    category_counts: Mapping[str, int]
    severity_counts: Mapping[str, int]
    status_counts: Mapping[str, int]
    source_counts: Mapping[str, int]
    patterns: tuple[OperationalPattern, ...]
    recommendations: tuple[OperationalRecommendation, ...]
    rule_candidates: tuple[OperationalCandidate, ...]
    standard_candidates: tuple[OperationalCandidate, ...]
    unresolved_record_ids: tuple[str, ...]
    interface_version: str = OPERATIONAL_INTERFACE_VERSION
    schema_version: int = OPERATIONAL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        """Return a detached summary safe for storage and upper-layer delivery."""
        return copy.deepcopy(asdict(self))
