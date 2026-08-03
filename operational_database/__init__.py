"""Universal Learning Engine v1.08 operational database public API."""

from .contracts import (
    OPERATIONAL_INTERFACE_VERSION,
    OPERATIONAL_SCHEMA_VERSION,
    ManagerCapabilityDefinition,
    OperationalDataPlane,
    OperationalQuery,
    OperationalRecord,
    OperationalRecordInput,
    OperationalReportSink,
    RecordCategory,
    RecordSeverity,
    RecordStatus,
    RecordTypeDefinition,
)
from .data_plane import SQLiteOperationalDataPlane
from .database import DEFAULT_OPERATIONAL_DATABASE_PATH, OperationalDatabase
from .errors import (
    OperationalContractError,
    OperationalDatabaseError,
    OperationalRegistryError,
    OperationalReportError,
    OperationalStorageError,
    OperationalValidationError,
    PersonalSecretaryIntegrationError,
)
from .manager import DatabaseManager
from .personal_secretary import (
    PERSONAL_SECRETARY_CAPABILITY_ID,
    PersonalSecretaryCoreCapability,
    PersonalSecretaryIntegration,
)
from .registry import (
    DatabaseManagerRegistry,
    OperationalRecordRegistry,
    default_manager_registry,
    default_record_registry,
)
from .reporting import (
    OperationalCandidate,
    OperationalPattern,
    OperationalRecommendation,
    OperationalReport,
)

__all__ = [
    "DEFAULT_OPERATIONAL_DATABASE_PATH",
    "DatabaseManager",
    "DatabaseManagerRegistry",
    "ManagerCapabilityDefinition",
    "OPERATIONAL_INTERFACE_VERSION",
    "OPERATIONAL_SCHEMA_VERSION",
    "OperationalCandidate",
    "OperationalContractError",
    "OperationalDataPlane",
    "OperationalDatabase",
    "OperationalDatabaseError",
    "OperationalPattern",
    "OperationalQuery",
    "OperationalRecommendation",
    "OperationalRecord",
    "OperationalRecordInput",
    "OperationalRecordRegistry",
    "OperationalRegistryError",
    "OperationalReport",
    "OperationalReportError",
    "OperationalReportSink",
    "OperationalStorageError",
    "OperationalValidationError",
    "PERSONAL_SECRETARY_CAPABILITY_ID",
    "PersonalSecretaryCoreCapability",
    "PersonalSecretaryIntegration",
    "PersonalSecretaryIntegrationError",
    "RecordCategory",
    "RecordSeverity",
    "RecordStatus",
    "RecordTypeDefinition",
    "SQLiteOperationalDataPlane",
    "default_manager_registry",
    "default_record_registry",
]
