from decimal import Decimal

from pydantic import BaseModel, Field


class RecoveryAnalytics(BaseModel):
    """
    Aggregated business metrics for the revenue recovery pipeline.

    These metrics are calculated from persisted recovery audit records.
    """

    total_records: int = Field(
        ge=0,
    )

    completed_records: int = Field(
        ge=0,
    )

    failed_pipeline_records: int = Field(
        ge=0,
    )

    total_amount_at_risk: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    total_expected_recovery_value: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    total_recovered_amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    recovery_rate: float = Field(
        default=0.0,
        ge=0,
    )

    records_requiring_review: int = Field(
        default=0,
        ge=0,
    )

    approved_actions: int = Field(
        default=0,
        ge=0,
    )

    blocked_actions: int = Field(
        default=0,
        ge=0,
    )

    execution_successful: int = Field(
        default=0,
        ge=0,
    )

    execution_failed: int = Field(
        default=0,
        ge=0,
    )


class DistributionMetric(BaseModel):
    """
    Represents the distribution of records across a category.

    Examples:
    - Recovery actions
    - Root causes
    - Governance decisions
    - Execution statuses
    """

    category: str = Field(
        ...,
        min_length=1,
    )

    count: int = Field(
        ...,
        ge=0,
    )


class AnalyticsDashboard(BaseModel):
    """
    Complete analytics response for the revenue recovery system.

    Combines high-level business metrics with categorical
    distributions useful for dashboards and monitoring.
    """

    summary: RecoveryAnalytics

    root_cause_distribution: list[DistributionMetric]

    recovery_action_distribution: list[DistributionMetric]

    governance_distribution: list[DistributionMetric]

    execution_distribution: list[DistributionMetric]