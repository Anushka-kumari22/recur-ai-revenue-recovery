from enum import Enum

from pydantic import BaseModel, Field


class RootCause(str, Enum):
    TEMPORARY_TECHNICAL_ISSUE = "temporary_technical_issue"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    PAYMENT_INSTRUMENT_EXPIRED = "payment_instrument_expired"
    MANDATE_ISSUE = "mandate_issue"
    BANK_DECLINE = "bank_decline"
    RISK_REVIEW_REQUIRED = "risk_review_required"
    UNKNOWN = "unknown"


class DiagnosisSource(str, Enum):
    RULE_BASED = "rule_based"
    LLM = "llm"


class DiagnosisResult(BaseModel):
    """
    Canonical diagnosis produced for a failed payment.

    This object separates the observed failure signal from the
    application's inferred root cause.
    """

    root_cause: RootCause

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the diagnosis",
    )

    source: DiagnosisSource

    reasoning: str = Field(
        ...,
        min_length=1,
        description="Explanation for the diagnosis",
    )