from datetime import datetime
from decimal import Decimal
from typing import Optional

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


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "recur-ai-revenue-recovery"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.now)


class DiagnosisResponse(BaseModel):
    root_cause: str
    confidence: float
    reasoning: Optional[str] = None
    source: Optional[str] = None


class RecoveryPlanResponse(BaseModel):
    action: str
    expected_recovery_probability: Optional[float] = None
    expected_recovery_value: Decimal = Decimal("0")
    scheduled_for: Optional[datetime] = None
    reasoning: Optional[str] = None


class GovernanceResponse(BaseModel):
    decision: str
    reason: str
    message: Optional[str] = None


class ExecutionResponse(BaseModel):
    status: Optional[str] = None
    detail: Optional[str] = None
    provider_reference: Optional[str] = None
    recovered_amount: Decimal = Decimal("0")


class PipelineResponse(BaseModel):
    record_id: str
    pipeline_status: str
    diagnosis: Optional[DiagnosisResponse] = None
    recovery_plan: Optional[RecoveryPlanResponse] = None
    governance: Optional[GovernanceResponse] = None
    execution: Optional[ExecutionResponse] = None
    error_message: Optional[str] = None
    processed_at: datetime = Field(default_factory=datetime.now)


class OverallMetrics(BaseModel):
    total_records: int
    completed_records: int
    blocked_records: int
    requires_review_records: int
    total_amount_at_risk: Decimal
    expected_recovery_value: Decimal
    total_recovered_amount: Decimal
    recovery_rate_pct: float


class DistributionEntry(BaseModel):
    label: str
    count: int


class AnalyticsDashboardResponse(BaseModel):
    overall: OverallMetrics
    root_cause_distribution: list[DistributionEntry]
    recovery_action_distribution: list[DistributionEntry]
    generated_at: datetime = Field(default_factory=datetime.now)


class ErrorDetail(BaseModel):
    error_code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str
    errors: Optional[list[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)