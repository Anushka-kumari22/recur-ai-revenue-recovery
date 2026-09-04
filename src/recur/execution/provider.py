"""
Payment provider abstraction.

The execution layer depends only on this interface, never directly on a
specific payment provider's SDK or implementation.

This allows SimulatorProvider to be used for local development and testing,
while a future real provider can implement the same interface without
requiring changes to the core execution logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from pydantic import BaseModel, Field


class ProviderResult(BaseModel):
    """
    Uniform result returned by every payment provider implementation.
    """

    success: bool

    provider_reference: str | None = None

    detail: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation of the provider result",
    )


class PaymentProvider(ABC):
    """
    Abstract interface for payment provider implementations.

    Every provider must support retrying a payment and sending a
    customer-facing notification.
    """

    @abstractmethod
    def create_retry(
        self,
        record_id: str,
        amount: Decimal,
        idempotency_key: str,
    ) -> ProviderResult:
        """
        Attempt to recover a failed payment.

        Implementations must handle the same idempotency key safely and
        return a ProviderResult rather than exposing provider-specific data.
        """
        raise NotImplementedError

    @abstractmethod
    def send_notification(
        self,
        record_id: str,
        message: str,
    ) -> ProviderResult:
        """
        Send a customer-facing recovery notification.

        Implementations should return a ProviderResult describing the
        delivery outcome.
        """
        raise NotImplementedError