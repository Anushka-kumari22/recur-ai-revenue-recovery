from datetime import datetime, timezone
from decimal import Decimal

from recur.diagnosis import DiagnosisResult, RootCause
from recur.governance import (
    GovernanceDecision,
    GovernanceReason,
    evaluate_recovery_plan,
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
    status=PaymentStatus.FAILED,
    attempt_number=0,
    customer_contact_count=0,
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
        customer_contact_count=customer_contact_count,
        failed_at=datetime.now(timezone.utc),
        days_since_failure=0,
        status=status,
    )


def create_diagnosis():
    return DiagnosisResult(
        root_cause=RootCause.TEMPORARY_TECHNICAL_ISSUE,
        confidence=0.90,
        reasoning="A network timeout indicates a temporary technical issue.",
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


def test_normal_recovery_plan_is_approved():
    record = create_record()

    plan = create_plan(
        RecoveryAction.RETRY_PAYMENT
    )

    result = evaluate_recovery_plan(
        record,
        plan,
    )

    assert result.decision == GovernanceDecision.APPROVED
    assert result.reason == GovernanceReason.ACTION_APPROVED


def test_non_failed_payment_is_blocked():
    record = create_record(
        status=PaymentStatus.RECOVERED
    )

    plan = create_plan(
        RecoveryAction.RETRY_PAYMENT
    )

    result = evaluate_recovery_plan(
        record,
        plan,
    )

    assert result.decision == GovernanceDecision.BLOCKED
    assert result.reason == GovernanceReason.PAYMENT_NOT_FAILED


def test_retry_limit_is_enforced():
    record = create_record(
        attempt_number=3
    )

    plan = create_plan(
        RecoveryAction.RETRY_PAYMENT
    )

    result = evaluate_recovery_plan(
        record,
        plan,
    )

    assert result.decision == GovernanceDecision.BLOCKED
    assert result.reason == GovernanceReason.RETRY_LIMIT_EXCEEDED


def test_retry_later_also_respects_retry_limit():
    record = create_record(
        attempt_number=3
    )

    plan = create_plan(
        RecoveryAction.RETRY_LATER
    )

    result = evaluate_recovery_plan(
        record,
        plan,
    )

    assert result.decision == GovernanceDecision.BLOCKED
    assert result.reason == GovernanceReason.RETRY_LIMIT_EXCEEDED


def test_customer_contact_limit_is_enforced():
    record = create_record(
        customer_contact_count=3
    )

    plan = create_plan(
        RecoveryAction.REQUEST_PAYMENT_METHOD_UPDATE
    )

    result = evaluate_recovery_plan(
        record,
        plan,
    )

    assert result.decision == GovernanceDecision.BLOCKED
    assert result.reason == GovernanceReason.CONTACT_LIMIT_EXCEEDED


def test_mandate_renewal_respects_contact_limit():
    record = create_record(
        customer_contact_count=3
    )

    plan = create_plan(
        RecoveryAction.REQUEST_MANDATE_RENEWAL
    )

    result = evaluate_recovery_plan(
        record,
        plan,
    )

    assert result.decision == GovernanceDecision.BLOCKED
    assert result.reason == GovernanceReason.CONTACT_LIMIT_EXCEEDED


def test_risk_review_requires_human_review():
    record = create_record()

    plan = create_plan(
        RecoveryAction.ESCALATE_FOR_REVIEW
    )

    result = evaluate_recovery_plan(
        record,
        plan,
    )

    assert (
        result.decision
        == GovernanceDecision.REQUIRES_REVIEW
    )

    assert (
        result.reason
        == GovernanceReason.RISK_REVIEW_REQUIRED
    )


def test_stop_recovery_is_blocked():
    record = create_record()

    plan = create_plan(
        RecoveryAction.STOP_RECOVERY
    )

    result = evaluate_recovery_plan(
        record,
        plan,
    )

    assert result.decision == GovernanceDecision.BLOCKED
    assert result.reason == GovernanceReason.RECOVERY_STOPPED