"""Stable errors for the v1.08 operational data boundary."""


class OperationalDatabaseError(Exception):
    """Base class for operational database failures."""


class OperationalContractError(OperationalDatabaseError):
    """Raised when caller data violates the public contract."""


class OperationalValidationError(OperationalContractError):
    """Raised when an operational record cannot be validated."""


class OperationalRegistryError(OperationalContractError):
    """Raised when a registry definition is invalid or ambiguous."""


class OperationalStorageError(OperationalDatabaseError):
    """Raised when the data plane cannot complete an atomic operation."""


class OperationalReportError(OperationalDatabaseError):
    """Raised when an operational report cannot be generated or stored."""


class PersonalSecretaryIntegrationError(OperationalDatabaseError):
    """Raised when the Personal Secretary reporting boundary is unavailable."""
