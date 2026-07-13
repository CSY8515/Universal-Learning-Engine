"""Connection-only boundary for future Living OS integration."""

from abc import ABC, abstractmethod

from .api import ExpansionAPI


class LivingOSIntegrationInterface(ABC):
    """Define connection state without implementing any Living OS behavior."""

    @property
    @abstractmethod
    def connected(self) -> bool:
        """Report whether the adapter considers itself connected."""

    @abstractmethod
    def connect(self, expansion_api: ExpansionAPI) -> None:
        """Bind an adapter to an Expansion API instance."""

    @abstractmethod
    def disconnect(self) -> None:
        """Remove the adapter's Expansion API binding."""
