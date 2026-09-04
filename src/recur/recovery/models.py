from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from recur.diagnosis import DiagnosisResult


class RecoveryAction(str, Enum):
    RETRY_PAYMENT = "retry_payment"
    RETRY_LATER = "retry_later"
    REQUEST_PAYMENT_METHOD_UPDATE = "request_payment_method_update"
    REQUEST_MANDATE_RENEWAL = "request_mandate_renewal"
    ESCALATE_FOR_REVIEW = "escalate_for_review"
    STOP_RECOVERY = "stop_recovery"


class RecoveryPlan(BaseModel):
    """
    Structured recovery recommendation for a failed payment.

    This object is a recommendation only. A later governance layer
    determines whether the action may actually be executed.
    """

    action: RecoveryAction

    diagnosis: DiagnosisResult

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    scheduled_for: datetime | None = None

    expected_recovery_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    expected_recovery_value: Decimal = Field(
        ...,
        ge=0,
    )

    reasoning: str = Field(
        ...,
        min_length=1,
    )