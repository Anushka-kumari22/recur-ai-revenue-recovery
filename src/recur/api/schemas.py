from decimal import Decimal

from pydantic import BaseModel, Field

from recur.models import (
    FailureType,
    PaymentMethod,
)


class FailureRecordRequest(BaseModel):
    """
    API request model representing a failed payment that
    should be processed through the recovery pipeline.
    """

    record_id: str = Field(
        ...,
        min_length=1,
    )

    customer_id: str = Field(
        ...,
        min_length=1,
    )

    subscription_id: str = Field(
        ...,
        min_length=1,
    )

    amount: Decimal = Field(
        ...,
        gt=0,
    )

    currency: str = Field(
        ...,
        min_length=1,
    )

    failure_type: FailureType

    payment_method: PaymentMethod

    attempt_number: int = Field(
        default=0,
        ge=0,
    )

    customer_contact_count: int = Field(
        default=0,
        ge=0,
    )