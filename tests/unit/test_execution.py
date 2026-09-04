from datetime import datetime, timezone
from decimal import Decimal

from recur.diagnosis import DiagnosisResult, RootCause
from recur.execution import (
    ExecutionStatus,
    SimulatorProvider,
    execute_recovery_plan,
)
from recur.governance import (
    GovernanceDecision,
    GovernanceReason,
    GovernanceResult,
)
from recur.models import (
    FailureRecord,
    FailureType,
    MandateStatus,
    PaymentMethod,
    PaymentStatus,
)
from recur.recovery import (
    RecoveryAction,
    RecoveryPlan,
)


def create_record(
    *,
    attempt_number=0,
):
    return FailureRecord(
        record_id="record_001",
        customer_id="customer_001",
        subscription_id="subscription_001",
        amount=Decimal("1500.00"),
        currency="INR",
        failure_type=FailureType.NETWORK_TIMEOUT,
        payment_method=PaymentMethod.UPI,
        attempt_number=attempt_number,
        mandate_status=MandateStatus.ACTIVE,
        customer_contact_count=0,
        failed_at=datetime.now(timezone.utc),
        days_since_failure=0,
        status=PaymentStatus.FAILED,
    )


def create_diagnosis():
    return DiagnosisResult(
        root_cause=RootCause.TEMPORARY_TECHNICAL_ISSUE,
        confidence=0.90,
        reasoning="Test diagnosis.",
        source="rule_based",
    )


def create_plan(action):
    return RecoveryPlan(
        action=action,
        diagnosis=create_diagnosis(),
        confidence=0.90,
        scheduled_for=None,
        expected_recovery_probability=0.80,
        expected_recovery_value=Decimal("1200.00"),
        reasoning="Test recovery plan.",
    )


def create_governance_result(
    decision,
    reason=GovernanceReason.ACTION_APPROVED,
):
    return GovernanceResult(
        decision=decision,
        reason=reason,
        message="Test governance result.",
    )


def test_approved_retry_is_executed_successfully():
    record = create_record()

    plan = create_plan(
        RecoveryAction.RETRY_PAYMENT
    )

    governance_result = create_governance_result(
        GovernanceDecision.APPROVED
    )

    provider = SimulatorProvider()

    result = execute_recovery_plan(
        record,
        plan,
        governance_result,
        provider,
    )

    assert result.status == ExecutionStatus.SUCCESSFUL
    assert result.recovered_amount == Decimal("1500.00")
    assert result.provider_reference is not None


def test_blocked_action_is_skipped():
    record = create_record()

    plan = create_plan(
        RecoveryAction.RETRY_PAYMENT
    )

    governance_result = create_governance_result(
        GovernanceDecision.BLOCKED,
        GovernanceReason.RETRY_LIMIT_EXCEEDED,
    )

    provider = SimulatorProvider()

    result = execute_recovery_plan(
        record,
        plan,
        governance_result,
        provider,
    )

    assert result.status == ExecutionStatus.SKIPPED
    assert result.recovered_amount == Decimal("0")


def test_human_review_action_is_not_executed():
    record = create_record()

    plan = create_plan(
        RecoveryAction.ESCALATE_FOR_REVIEW
    )

    governance_result = create_governance_result(
        GovernanceDecision.REQUIRES_REVIEW,
        GovernanceReason.RISK_REVIEW_REQUIRED,
    )

    provider = SimulatorProvider()

    result = execute_recovery_plan(
        record,
        plan,
        governance_result,
        provider,
    )

    assert (
        result.status
        == ExecutionStatus.REQUIRES_HUMAN_REVIEW
    )

    assert result.recovered_amount == Decimal("0")


def test_payment_method_update_sends_notification():
    record = create_record()

    plan = create_plan(
        RecoveryAction.REQUEST_PAYMENT_METHOD_UPDATE
    )

    governance_result = create_governance_result(
        GovernanceDecision.APPROVED
    )

    provider = SimulatorProvider()

    result = execute_recovery_plan(
        record,
        plan,
        governance_result,
        provider,
    )

    assert result.status == ExecutionStatus.SUCCESSFUL
    assert result.recovered_amount == Decimal("0")
    assert result.provider_reference is not None


def test_mandate_renewal_sends_notification():
    record = create_record()

    plan = create_plan(
        RecoveryAction.REQUEST_MANDATE_RENEWAL
    )

    governance_result = create_governance_result(
        GovernanceDecision.APPROVED
    )

    provider = SimulatorProvider()

    result = execute_recovery_plan(
        record,
        plan,
        governance_result,
        provider,
    )

    assert result.status == ExecutionStatus.SUCCESSFUL
    assert result.recovered_amount == Decimal("0")


def test_execution_has_deterministic_idempotency_key():
    record = create_record(
        attempt_number=2
    )

    plan = create_plan(
        RecoveryAction.RETRY_PAYMENT
    )

    governance_result = create_governance_result(
        GovernanceDecision.APPROVED
    )

    provider = SimulatorProvider()

    result = execute_recovery_plan(
        record,
        plan,
        governance_result,
        provider,
    )

    assert (
        result.idempotency_key
        == "record_001:2:retry_payment"
    )