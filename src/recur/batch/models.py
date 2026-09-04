from decimal import Decimal

from pydantic import BaseModel, Field

from recur.orchestration import PipelineResult


class BatchProcessingResult(BaseModel):
    """
    Aggregated result produced after processing a collection
    of failed payment records through the recovery pipeline.
    """

    results: list[PipelineResult] = Field(
        default_factory=list,
        description="Individual pipeline results",
    )

    total_records: int = Field(
        default=0,
        ge=0,
    )

    completed_records: int = Field(
        default=0,
        ge=0,
    )

    blocked_records: int = Field(
        default=0,
        ge=0,
    )

    records_requiring_review: int = Field(
        default=0,
        ge=0,
    )

    failed_records: int = Field(
        default=0,
        ge=0,
        description="Records that encountered processing errors",
    )

    total_amount_at_risk: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    total_expected_recovery_value: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )