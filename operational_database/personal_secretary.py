"""OS Ecosystem Personal Secretary Core Capability reporting boundary."""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime, timezone

from .contracts import OPERATIONAL_INTERFACE_VERSION, OperationalReportSink
from .errors import PersonalSecretaryIntegrationError


PERSONAL_SECRETARY_CAPABILITY_ID = (
    "universal-learning-engine.operational-reporting"
)


class PersonalSecretaryCoreCapability(ABC):
    """Port implemented by the OS Ecosystem Personal Secretary Core."""

    @abstractmethod
    def receive_operational_report(
        self, capability_id: str, envelope: Mapping[str, object]
    ) -> object:
        """Receive one versioned summary report envelope."""


class PersonalSecretaryIntegration(OperationalReportSink):
    """Connect Database Manager reporting to a Personal Secretary Core port."""

    def __init__(self) -> None:
        self._core: PersonalSecretaryCoreCapability | None = None

    @property
    def connected(self) -> bool:
        return self._core is not None

    def connect(self, core: PersonalSecretaryCoreCapability) -> None:
        if not isinstance(core, PersonalSecretaryCoreCapability):
            raise PersonalSecretaryIntegrationError(
                "core must implement PersonalSecretaryCoreCapability"
            )
        self._core = core

    def disconnect(self) -> None:
        self._core = None

    def publish_operational_report(self, report: Mapping[str, object]) -> object:
        if self._core is None:
            raise PersonalSecretaryIntegrationError(
                "Personal Secretary integration is not connected"
            )
        if not isinstance(report, Mapping):
            raise PersonalSecretaryIntegrationError(
                "operational report must be a mapping"
            )
        required = {"report_id", "generated_at", "category_counts"}
        if not required.issubset(report):
            raise PersonalSecretaryIntegrationError(
                "operational report is missing required summary fields"
            )
        envelope = {
            "capability_id": PERSONAL_SECRETARY_CAPABILITY_ID,
            "interface_version": OPERATIONAL_INTERFACE_VERSION,
            "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "report": copy.deepcopy(dict(report)),
        }
        return self._core.receive_operational_report(
            PERSONAL_SECRETARY_CAPABILITY_ID, envelope
        )
