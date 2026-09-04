from decimal import Decimal

from recur.governance import GovernanceDecision
from recur.models import FailureRecord
from recur.orchestration import PipelineStatus, process_failure

from recur.batch.models import BatchProcessingResult


def process_failure_records(
    records: list[FailureRecord],
) -> BatchProcessingResult:
    """
    Process multiple failed payment records through the complete
    revenue recovery pipeline.

    Every record passes through:

        Diagnosis
            ↓
        Recovery Planning
            ↓
        Governance
            ↓
        Pipeline Result

    Individual record-processing errors are isolated so that one
    invalid record does not stop the entire batch.
    """

    results = []

    total_records = len(records)
    completed_records = 0
    blocked_records = 0
    records_requiring_review = 0
    failed_records = 0

    total_amount_at_risk = Decimal("0.00")
    total_expected_recovery_value = Decimal("0.00")

    for record in records:
        total_amount_at_risk += record.amount

        try:
            result = process_failure(record)
            results.append(result)

            if result.status == PipelineStatus.COMPLETED:
                completed_records += 1

            if result.governance_result is not None:
                decision = result.governance_result.decision

                if decision == GovernanceDecision.BLOCKED:
                    blocked_records += 1

                elif (
                    decision
                    == GovernanceDecision.REQUIRES_REVIEW
                ):
                    records_requiring_review += 1

            if result.recovery_plan is not None:
                total_expected_recovery_value += (
                    result.recovery_plan.expected_recovery_value
                )

        except Exception:
            failed_records += 1

    return BatchProcessingResult(
        results=results,
        total_records=total_records,
        completed_records=completed_records,
        blocked_records=blocked_records,
        records_requiring_review=records_requiring_review,
        failed_records=failed_records,
        total_amount_at_risk=total_amount_at_risk.quantize(
            Decimal("0.01")
        ),
        total_expected_recovery_value=(
            total_expected_recovery_value.quantize(
                Decimal("0.01")
            )
        ),
    )