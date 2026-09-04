from datetime import timedelta
from decimal import Decimal

from recur.diagnosis import RootCause
from recur.models import FailureRecord
from recur.recovery.models import (
    RecoveryAction,
    RecoveryPlan,
)


RECOVERY_PROBABILITIES = {
    RecoveryAction.RETRY_PAYMENT: Decimal("0.80"),
    RecoveryAction.RETRY_LATER: Decimal("0.60"),
    RecoveryAction.REQUEST_PAYMENT_METHOD_UPDATE: Decimal("0.50"),
    RecoveryAction.REQUEST_MANDATE_RENEWAL: Decimal("0.55"),
    RecoveryAction.ESCALATE_FOR_REVIEW: Decimal("0.00"),
    RecoveryAction.STOP_RECOVERY: Decimal("0.00"),
}


def calculate_expected_recovery_value(
    amount: Decimal,
    recovery_probability: Decimal,
) -> Decimal:
    """
    Calculate the expected recoverable revenue.

    Expected value = failed payment amount × probability of recovery.
    """

    return (amount * recovery_probability).quantize(
        Decimal("0.01")
    )


def create_recovery_plan(
    record: FailureRecord,
    diagnosis,
) -> RecoveryPlan:
    """
    Create a deterministic recovery recommendation from a payment
    failure and its diagnosis.

    This function does not execute a payment action.
    """

    scheduled_for = None

    if diagnosis.root_cause == RootCause.TEMPORARY_TECHNICAL_ISSUE:
        action = RecoveryAction.RETRY_PAYMENT

        scheduled_for = (
            record.failed_at + timedelta(minutes=30)
        )

        reasoning = (
            "The failure appears temporary, so a controlled "
            "payment retry is recommended."
        )

    elif diagnosis.root_cause == RootCause.INSUFFICIENT_FUNDS:
        action = RecoveryAction.RETRY_LATER

        scheduled_for = (
            record.failed_at + timedelta(days=1)
        )

        reasoning = (
            "The customer may need time to restore sufficient "
            "account funds before another payment attempt."
        )

    elif diagnosis.root_cause == RootCause.PAYMENT_INSTRUMENT_EXPIRED:
        action = (
            RecoveryAction.REQUEST_PAYMENT_METHOD_UPDATE
        )

        reasoning = (
            "The existing payment instrument is expired and "
            "must be updated before recovery can continue."
        )

    elif diagnosis.root_cause == RootCause.MANDATE_ISSUE:
        action = RecoveryAction.REQUEST_MANDATE_RENEWAL

        reasoning = (
            "The payment mandate requires renewal before "
            "future payment attempts can proceed."
        )

    elif diagnosis.root_cause == RootCause.BANK_DECLINE:
        action = RecoveryAction.RETRY_LATER

        scheduled_for = (
            record.failed_at + timedelta(hours=12)
        )

        reasoning = (
            "The bank declined the payment, so a delayed retry "
            "is recommended instead of an immediate retry."
        )

    elif diagnosis.root_cause == RootCause.RISK_REVIEW_REQUIRED:
        action = RecoveryAction.ESCALATE_FOR_REVIEW

        reasoning = (
            "The payment is associated with a risk hold and "
            "requires review before further recovery actions."
        )

    else:
        action = RecoveryAction.STOP_RECOVERY

        reasoning = (
            "The system cannot determine a sufficiently reliable "
            "recovery action."
        )

    probability = RECOVERY_PROBABILITIES[action]

    expected_value = calculate_expected_recovery_value(
        record.amount,
        probability,
    )

    return RecoveryPlan(
        action=action,
        diagnosis=diagnosis,
        confidence=diagnosis.confidence,
        scheduled_for=scheduled_for,
        expected_recovery_probability=float(probability),
        expected_recovery_value=expected_value,
        reasoning=reasoning,
    )