from datetime import datetime, timezone
from decimal import Decimal

from recur.governance import GovernanceDecision
from recur.models import (
    FailureRecord,
    FailureType,
    MandateStatus,
    PaymentMethod,
)
from recur.orchestration import (
    PipelineStatus,
    process_failure,
)
from recur.recovery import RecoveryAction


def create_record(
    *,
    failure_type=FailureType.NETWORK_TIMEOUT,
    mandate_status=MandateStatus.ACTIVE,
):
    return FailureRecord(
        record_id="pipeline_record_001",
        customer_id="pipeline_customer_001",
        subscription_id="pipeline_subscription_001",
        amount=Decimal("2000.00"),
        currency="INR",
        failure_type=failure_type,
        payment_method=PaymentMethod.UPI,
        attempt_number=0,
        mandate_status=mandate_status,
        customer_contact_count=0,
        failed_at=datetime.now(timezone.utc),
        days_since_failure=0,
    )


def test_pipeline_processes_network_timeout():
    record = create_record(
        failure_type=FailureType.NETWORK_TIMEOUT
    )

    result = process_failure(record)

    assert result.status == PipelineStatus.COMPLETED
    assert result.diagnosis is not None
    assert result.recovery_plan is not None
    assert result.governance_result is not None

    assert (
        result.recovery_plan.action
        == RecoveryAction.RETRY_PAYMENT
    )

    assert (
        result.governance_result.decision
        == GovernanceDecision.APPROVED
    )


def test_pipeline_processes_insufficient_funds():
    record = create_record(
        failure_type=FailureType.INSUFFICIENT_FUNDS
    )

    result = process_failure(record)

    assert result.status == PipelineStatus.COMPLETED

    assert (
        result.recovery_plan.action
        == RecoveryAction.RETRY_LATER
    )


def test_pipeline_processes_expired_card():
    record = create_record(
        failure_type=FailureType.CARD_EXPIRED
    )

    result = process_failure(record)

    assert result.status == PipelineStatus.COMPLETED

    assert (
        result.recovery_plan.action
        == RecoveryAction.REQUEST_PAYMENT_METHOD_UPDATE
    )


def test_pipeline_processes_expired_mandate():
    record = create_record(
        failure_type=FailureType.MANDATE_EXPIRED,
        mandate_status=MandateStatus.EXPIRED,
    )

    result = process_failure(record)

    assert result.status == PipelineStatus.COMPLETED

    assert (
        result.recovery_plan.action
        == RecoveryAction.REQUEST_MANDATE_RENEWAL
    )


def test_pipeline_sends_risk_hold_for_review():
    record = create_record(
        failure_type=FailureType.RISK_HOLD
    )

    result = process_failure(record)

    assert result.status == PipelineStatus.COMPLETED

    assert (
        result.recovery_plan.action
        == RecoveryAction.ESCALATE_FOR_REVIEW
    )

    assert (
        result.governance_result.decision
        == GovernanceDecision.REQUIRES_REVIEW
    )