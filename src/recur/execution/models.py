from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    PENDING_EXECUTION = "pending_execution"
    EXECUTED = "executed"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    SKIPPED = "skipped"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


class ExecutionResult(BaseModel):
    """
    Result of attempting to execute a recovery action.

    The execution layer does not decide whether an action is allowed.
    Governance makes that decision. Execution only enforces the decision
    and records the resulting outcome.
    """

    record_id: str = Field(
        ...,
        min_length=1,
    )

    action: str = Field(
        ...,
        min_length=1,
    )

    status: ExecutionStatus

    executed_at: datetime

    idempotency_key: str = Field(
        ...,
        min_length=1,
    )

    provider_reference: str | None = None

    detail: str = Field(
        ...,
        min_length=1,
    )

    recovered_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )