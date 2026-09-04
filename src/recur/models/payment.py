from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class PaymentStatus(str, Enum):
    FAILED = "failed"
    PENDING = "pending"
    RECOVERED = "recovered"
    ABANDONED = "abandoned"


class PaymentMethod(str, Enum):
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    EMANDATE = "emandate"
    WALLET = "wallet"
    OTHER = "other"


class MandateStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    NOT_APPLICABLE = "not_applicable"


class FailureType(str, Enum):
    BANK_DECLINE = "bank_decline"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    NETWORK_TIMEOUT = "network_timeout"
    CARD_EXPIRED = "card_expired"
    MANDATE_EXPIRED = "mandate_expired"
    RISK_HOLD = "risk_hold"
    UNKNOWN = "unknown"


class FailureRecord(BaseModel):
    """
    Canonical representation of a failed payment inside the application.

    This model acts as the validated data contract between ingestion,
    diagnosis, strategy, governance, execution, and analytics layers.
    """

    record_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for this failure record",
    )

    customer_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the customer",
    )

    subscription_id: str = Field(
        ...,
        min_length=1,
        description="Subscription associated with the failed payment",
    )

    amount: Decimal = Field(
        ...,
        gt=0,
        description="Amount at risk from the failed payment",
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="ISO currency code",
    )

    failure_type: FailureType = Field(
        ...,
        description="Observed payment failure category",
    )

    payment_method: PaymentMethod = Field(
        default=PaymentMethod.OTHER,
    )

    attempt_number: int = Field(
        default=0,
        ge=0,
        description="Number of recovery attempts already made",
    )

    mandate_status: MandateStatus = Field(
        default=MandateStatus.NOT_APPLICABLE,
    )

    customer_contact_count: int = Field(
        default=0,
        ge=0,
        description="Number of recovery contacts already sent",
    )

    failed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the payment failure occurred",
    )

    days_since_failure: int = Field(
        default=0,
        ge=0,
        description="Number of days since the payment failure",
    )

    status: PaymentStatus = Field(
        default=PaymentStatus.FAILED,
    )

    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional provider-specific metadata",
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("record_id", "customer_id", "subscription_id")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Identifier cannot be empty")

        return value