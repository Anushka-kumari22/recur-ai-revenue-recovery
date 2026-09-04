"""
Simulated payment provider for local development and testing.

This provider performs no real financial transaction and sends no real
customer communication.
"""

from decimal import Decimal

from recur.execution.provider import (
    PaymentProvider,
    ProviderResult,
)


class SimulatorProvider(PaymentProvider):
    """
    Deterministic simulated payment provider.

    Used during development and testing before connecting a real
    payment provider.
    """

    def create_retry(
        self,
        record_id: str,
        amount: Decimal,
        idempotency_key: str,
    ) -> ProviderResult:
        """
        Simulate a successful payment retry.

        No real payment is attempted.
        """

        provider_reference = (
            f"sim_retry_{record_id}_{idempotency_key}"
        )

        return ProviderResult(
            success=True,
            provider_reference=provider_reference,
            detail=(
                f"Simulated retry completed for record "
                f"{record_id}."
            ),
        )

    def send_notification(
        self,
        record_id: str,
        message: str,
    ) -> ProviderResult:
        """
        Simulate a successful customer notification.

        No real message is sent.
        """

        provider_reference = (
            f"sim_notification_{record_id}"
        )

        return ProviderResult(
            success=True,
            provider_reference=provider_reference,
            detail=(
                f"Simulated notification completed for record "
                f"{record_id}."
            ),
        )