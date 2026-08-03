"""Deterministic registries for v1.08 record types and manager capabilities."""

from __future__ import annotations

from .contracts import (
    ManagerCapabilityDefinition,
    RecordCategory,
    RecordSeverity,
    RecordTypeDefinition,
)
from .errors import OperationalRegistryError


def _registry_key(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OperationalRegistryError("registry key must be a non-empty string")
    return value.strip().casefold().replace("-", "_").replace(" ", "_")


class OperationalRecordRegistry:
    """Resolve the closed operational classification without inference."""

    def __init__(self) -> None:
        self._definitions: dict[RecordCategory, RecordTypeDefinition] = {}
        self._aliases: dict[str, RecordCategory] = {}

    def register(self, definition: RecordTypeDefinition) -> None:
        if not isinstance(definition, RecordTypeDefinition):
            raise OperationalRegistryError(
                "definition must be a RecordTypeDefinition"
            )
        if definition.category in self._definitions:
            raise OperationalRegistryError(
                f"record category {definition.category.value!r} is registered"
            )
        keys = {
            _registry_key(definition.category.value),
            *(_registry_key(alias) for alias in definition.aliases),
        }
        collision = next((key for key in keys if key in self._aliases), None)
        if collision:
            raise OperationalRegistryError(
                f"record category alias {collision!r} is registered"
            )
        self._definitions[definition.category] = definition
        for key in keys:
            self._aliases[key] = definition.category

    def resolve(self, value: RecordCategory | str) -> RecordTypeDefinition:
        if isinstance(value, RecordCategory):
            category = value
        else:
            category = self._aliases.get(_registry_key(value))
            if category is None:
                raise OperationalRegistryError(
                    f"unsupported record category {value!r}"
                )
        try:
            return self._definitions[category]
        except KeyError as exc:
            raise OperationalRegistryError(
                f"record category {category.value!r} is not registered"
            ) from exc

    def definitions(self) -> tuple[RecordTypeDefinition, ...]:
        return tuple(
            self._definitions[category]
            for category in sorted(self._definitions, key=lambda item: item.value)
        )


class DatabaseManagerRegistry:
    """Declare the fixed analytical capabilities owned by Database Manager."""

    def __init__(self) -> None:
        self._definitions: dict[str, ManagerCapabilityDefinition] = {}

    def register(self, definition: ManagerCapabilityDefinition) -> None:
        if not isinstance(definition, ManagerCapabilityDefinition):
            raise OperationalRegistryError(
                "definition must be a ManagerCapabilityDefinition"
            )
        key = _registry_key(definition.name)
        if key in self._definitions:
            raise OperationalRegistryError(
                f"manager capability {definition.name!r} is registered"
            )
        self._definitions[key] = ManagerCapabilityDefinition(
            name=key,
            description=definition.description.strip(),
        )

    def contains(self, name: str) -> bool:
        return _registry_key(name) in self._definitions

    def definitions(self) -> tuple[ManagerCapabilityDefinition, ...]:
        return tuple(self._definitions[key] for key in sorted(self._definitions))


def default_record_registry() -> OperationalRecordRegistry:
    registry = OperationalRecordRegistry()
    specifications = (
        (RecordCategory.SUCCESS, RecordSeverity.INFO, "Successful operation"),
        (RecordCategory.FAILURE, RecordSeverity.ERROR, "Failed operation"),
        (RecordCategory.ERROR, RecordSeverity.ERROR, "Runtime or provider error"),
        (RecordCategory.WARNING, RecordSeverity.WARNING, "Non-fatal warning"),
        (RecordCategory.INCIDENT, RecordSeverity.CRITICAL, "Operational incident"),
        (RecordCategory.RECOVERY, RecordSeverity.INFO, "Completed recovery"),
        (RecordCategory.ROLLBACK, RecordSeverity.WARNING, "Completed rollback"),
        (RecordCategory.VALIDATION_FAILURE, RecordSeverity.WARNING, "Validation failure"),
        (RecordCategory.EXECUTION_FAILURE, RecordSeverity.ERROR, "Execution failure"),
        (RecordCategory.INVALID_DATA, RecordSeverity.WARNING, "Invalid data"),
        (RecordCategory.REJECTED_DECISION, RecordSeverity.WARNING, "Rejected decision"),
        (RecordCategory.UNRESOLVED_ISSUE, RecordSeverity.ERROR, "Unresolved issue"),
    )
    for category, severity, description in specifications:
        registry.register(RecordTypeDefinition(category, severity, description))
    return registry


def default_manager_registry() -> DatabaseManagerRegistry:
    registry = DatabaseManagerRegistry()
    definitions = (
        ("data_validation", "Validate every record before persistence."),
        ("classification", "Resolve an explicit registered record category."),
        ("duplicate_control", "Preserve duplicates but exclude them from canonical analysis."),
        ("pattern_analysis", "Identify repeated canonical operational patterns."),
        ("operational_analysis", "Aggregate retained operational evidence."),
        ("recommendation", "Produce deterministic advisory actions."),
        ("rule_candidate", "Produce inactive rule candidates from evidence."),
        ("standard_candidate", "Produce inactive standard candidates from evidence."),
        ("operational_reporting", "Generate and retain upper-layer reports."),
    )
    for name, description in definitions:
        registry.register(ManagerCapabilityDefinition(name, description))
    return registry
