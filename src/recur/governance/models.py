from enum import Enum

from pydantic import BaseModel, Field


class GovernanceDecision(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"
    REQUIRES_REVIEW = "requires_review"


class GovernanceReason(str, Enum):
    PAYMENT_NOT_FAILED = "payment_not_failed"
    RETRY_LIMIT_EXCEEDED = "retry_limit_exceeded"
    CONTACT_LIMIT_EXCEEDED = "contact_limit_exceeded"
    RISK_REVIEW_REQUIRED = "risk_review_required"
    RECOVERY_STOPPED = "recovery_stopped"
    ACTION_APPROVED = "action_approved"


class GovernanceResult(BaseModel):
    """
    Result produced by the governance layer.

    Governance evaluates whether a recovery recommendation is
    allowed to proceed, blocked, or requires human review.
    """

    decision: GovernanceDecision

    reason: GovernanceReason

    message: str = Field(
        ...,
        min_length=1,
    )