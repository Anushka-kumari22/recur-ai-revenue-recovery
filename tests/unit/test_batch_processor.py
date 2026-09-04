from datetime import datetime, timezone
from decimal import Decimal

from recur.batch import process_failure_records
from recur.governance import GovernanceDecision
from recur.models import (
    FailureRecord,
    FailureType,
    MandateStatus,
    PaymentMethod,
)
from recur.orchestration import PipelineStatus
from recur.recovery import RecoveryAction


def create_record(
    *,
    record_id: str,
    failure_type: FailureType,
    amount: str = "1000.00",
):
    return FailureRecord(
        record_id=record_id,
        customer_id=f"customer_{record_id}",
        subscription_id=f"subscription_{record_id}",
        amount=Decimal(amount),
        currency="INR",
        failure_type=failure_type,
        payment_method=PaymentMethod.UPI,
        attempt_number=0,
        mandate_status=MandateStatus.ACTIVE,
        customer_contact_count=0,
        failed_at=datetime.now(timezone.utc),
        days_since_failure=0,
    )


def test_empty_batch():
    result = process_failure_records([])

    assert result.total_records == 0
    assert result.completed_records == 0
    assert result.failed_records == 0
    assert result.total_amount_at_risk == Decimal("0.00")
    assert result.total_expected_recovery_value == Decimal("0.00")
    assert result.results == []


def test_single_record_is_processed():
    record = create_record(
        record_id="001",
        failure_type=FailureType.NETWORK_TIMEOUT,
    )

    result = process_failure_records([record])

    assert result.total_records == 1
    assert result.completed_records == 1
    assert result.failed_records == 0
    assert len(result.results) == 1

    pipeline_result = result.results[0]

    assert pipeline_result.status == PipelineStatus.COMPLETED

    assert (
        pipeline_result.recovery_plan.action
        == RecoveryAction.RETRY_PAYMENT
    )


def test_multiple_records_are_processed():
    records = [
        create_record(
            record_id="001",
            failure_type=FailureType.NETWORK_TIMEOUT,
            amount="1000.00",
        ),
        create_record(
            record_id="002",
            failure_type=FailureType.INSUFFICIENT_FUNDS,
            amount="2000.00",
        ),
        create_record(
            record_id="003",
            failure_type=FailureType.RISK_HOLD,
            amount="3000.00",
        ),
    ]

    result = process_failure_records(records)

    assert result.total_records == 3
    assert result.completed_records == 3
    assert result.failed_records == 0
    assert len(result.results) == 3
    assert result.total_amount_at_risk == Decimal("6000.00")


def test_risk_hold_requires_review():
    record = create_record(
        record_id="risk_001",
        failure_type=FailureType.RISK_HOLD,
    )

    result = process_failure_records([record])

    assert result.records_requiring_review == 1

    pipeline_result = result.results[0]

    assert (
        pipeline_result.governance_result.decision
        == GovernanceDecision.REQUIRES_REVIEW
    )


def test_expected_recovery_value_is_aggregated():
    records = [
        create_record(
            record_id="001",
            failure_type=FailureType.NETWORK_TIMEOUT,
            amount="1000.00",
        ),
        create_record(
            record_id="002",
            failure_type=FailureType.RISK_HOLD,
            amount="1000.00",
        ),
    ]

    result = process_failure_records(records)

    assert result.total_expected_recovery_value == Decimal("800.00")