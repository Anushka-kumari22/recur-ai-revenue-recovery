from contextlib import nullcontext
from decimal import Decimal

from sqlalchemy import func, select

from recur.analytics.models import (
    AnalyticsDashboard,
    DistributionMetric,
    RecoveryAnalytics,
)
from recur.persistence.database import SessionLocal
from recur.persistence.models import RecoveryAuditRecord


def _decimal_or_zero(value) -> Decimal:
    """
    Convert a database aggregate result into Decimal.

    SQLite aggregate queries may return None when no records exist.
    """

    if value is None:
        return Decimal("0")

    return Decimal(str(value))


def _calculate_recovery_rate(
    recovered_amount: Decimal,
    total_amount_at_risk: Decimal,
) -> float:
    """
    Calculate the percentage of total amount recovered.
    """

    if total_amount_at_risk <= 0:
        return 0.0

    return round(
        float(
            (
                recovered_amount
                / total_amount_at_risk
            )
            * Decimal("100")
        ),
        2,
    )


def _get_distribution(
    session,
    column,
) -> list[DistributionMetric]:
    """
    Calculate the record distribution for a database column.
    """

    statement = (
        select(
            column,
            func.count(
                RecoveryAuditRecord.id
            ),
        )
        .where(column.is_not(None))
        .group_by(column)
        .order_by(
            func.count(
                RecoveryAuditRecord.id
            ).desc()
        )
    )

    rows = session.execute(
        statement
    ).all()

    return [
        DistributionMetric(
            category=str(category),
            count=count,
        )
        for category, count in rows
    ]


def get_analytics_dashboard(session=None) -> AnalyticsDashboard:
    """
    Generate a complete analytics dashboard from persisted
    recovery audit records.

    The dashboard contains:

    - Pipeline processing metrics
    - Financial recovery metrics
    - Governance metrics
    - Execution metrics
    - Root cause distribution
    - Recovery action distribution
    - Governance decision distribution
    - Execution status distribution
    """

    session_context = (
        SessionLocal()
        if session is None
        else nullcontext(session)
    )

    with session_context as session:

        # ----------------------------------------------
        # RECORD COUNTS
        # ----------------------------------------------

        total_records = session.scalar(
            select(
                func.count(
                    RecoveryAuditRecord.id
                )
            )
        ) or 0

        completed_records = session.scalar(
            select(
                func.count(
                    RecoveryAuditRecord.id
                )
            ).where(
                RecoveryAuditRecord.pipeline_status
                == "completed"
            )
        ) or 0

        failed_pipeline_records = session.scalar(
            select(
                func.count(
                    RecoveryAuditRecord.id
                )
            ).where(
                RecoveryAuditRecord.pipeline_status
                == "failed"
            )
        ) or 0

        # ----------------------------------------------
        # FINANCIAL METRICS
        # ----------------------------------------------

        total_amount_at_risk = _decimal_or_zero(
            session.scalar(
                select(
                    func.sum(
                        RecoveryAuditRecord.amount
                    )
                )
            )
        )

        total_expected_recovery_value = _decimal_or_zero(
            session.scalar(
                select(
                    func.sum(
                        RecoveryAuditRecord.expected_recovery_value
                    )
                )
            )
        )

        total_recovered_amount = _decimal_or_zero(
            session.scalar(
                select(
                    func.sum(
                        RecoveryAuditRecord.recovered_amount
                    )
                )
            )
        )

        recovery_rate = _calculate_recovery_rate(
            recovered_amount=total_recovered_amount,
            total_amount_at_risk=total_amount_at_risk,
        )

        # ----------------------------------------------
        # GOVERNANCE METRICS
        # ----------------------------------------------

        records_requiring_review = session.scalar(
            select(
                func.count(
                    RecoveryAuditRecord.id
                )
            ).where(
                RecoveryAuditRecord.governance_decision
                == "requires_review"
            )
        ) or 0

        approved_actions = session.scalar(
            select(
                func.count(
                    RecoveryAuditRecord.id
                )
            ).where(
                RecoveryAuditRecord.governance_decision
                == "approved"
            )
        ) or 0

        blocked_actions = session.scalar(
            select(
                func.count(
                    RecoveryAuditRecord.id
                )
            ).where(
                RecoveryAuditRecord.governance_decision
                == "blocked"
            )
        ) or 0

        # ----------------------------------------------
        # EXECUTION METRICS
        # ----------------------------------------------

        execution_successful = session.scalar(
            select(
                func.count(
                    RecoveryAuditRecord.id
                )
            ).where(
                RecoveryAuditRecord.execution_status
                == "successful"
            )
        ) or 0

        execution_failed = session.scalar(
            select(
                func.count(
                    RecoveryAuditRecord.id
                )
            ).where(
                RecoveryAuditRecord.execution_status
                == "failed"
            )
        ) or 0

        # ----------------------------------------------
        # DISTRIBUTIONS
        # ----------------------------------------------

        root_cause_distribution = _get_distribution(
            session,
            RecoveryAuditRecord.root_cause,
        )

        recovery_action_distribution = _get_distribution(
            session,
            RecoveryAuditRecord.recovery_action,
        )

        governance_distribution = _get_distribution(
            session,
            RecoveryAuditRecord.governance_decision,
        )

        execution_distribution = _get_distribution(
            session,
            RecoveryAuditRecord.execution_status,
        )

    summary = RecoveryAnalytics(
        total_records=total_records,
        completed_records=completed_records,
        failed_pipeline_records=failed_pipeline_records,
        total_amount_at_risk=total_amount_at_risk,
        total_expected_recovery_value=(
            total_expected_recovery_value
        ),
        total_recovered_amount=total_recovered_amount,
        recovery_rate=recovery_rate,
        records_requiring_review=records_requiring_review,
        approved_actions=approved_actions,
        blocked_actions=blocked_actions,
        execution_successful=execution_successful,
        execution_failed=execution_failed,
    )

    return AnalyticsDashboard(
        summary=summary,
        root_cause_distribution=(
            root_cause_distribution
        ),
        recovery_action_distribution=(
            recovery_action_distribution
        ),
        governance_distribution=(
            governance_distribution
        ),
        execution_distribution=(
            execution_distribution
        ),
    )