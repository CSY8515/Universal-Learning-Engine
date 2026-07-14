"""Stable errors raised by the Expansion Platform."""


class ExpansionError(Exception):
    """Base class for Expansion Platform failures."""


class PackContractError(ExpansionError, ValueError):
    """The supplied pack does not satisfy the common interface."""


class IncompatiblePackError(PackContractError):
    """The pack targets an unsupported Expansion Platform interface."""


class DuplicatePackError(ExpansionError):
    """The exact pack identity is already installed."""


class PackNotFoundError(ExpansionError, LookupError):
    """No installed pack matches the requested identity."""


class AmbiguousPackVersionError(ExpansionError, LookupError):
    """A pack id has multiple installed versions and needs exact selection."""


class PackLoadError(ExpansionError):
    """A pack lifecycle operation failed."""


class PackStateError(ExpansionError):
    """A pack lifecycle operation conflicts with its current state."""


class PackExecutionError(ExpansionError):
    """A pack execution or termination callback failed."""


class PackSessionNotFoundError(ExpansionError, LookupError):
    """No active Pack Session matches the requested session identity."""


class LivingOSIntegrationError(ExpansionError):
    """The Living OS connection interface was used in an invalid state."""
