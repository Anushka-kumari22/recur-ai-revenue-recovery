from datetime import datetime, timezone

from recur.execution.idempotency import (
    create_idempotency_key,
)
from recur.execution.models import (
    ExecutionResult,
    ExecutionStatus,
)
from recur.execution.provider import PaymentProvider
from recur.governance import (
    GovernanceDecision,
    GovernanceResult,
)
from recur.models import FailureRecord
from recur.recovery import (
    RecoveryAction,
    RecoveryPlan,
)


def execute_recovery_plan(
    record: FailureRecord,
    recovery_plan: RecoveryPlan,
    governance_result: GovernanceResult,
    provider: PaymentProvider,
) -> ExecutionResult:
    """
    Execute an approved recovery plan.

    Governance is always evaluated before execution. This function
    never overrides a governance decision.

    The function supports:
    - Payment retry operations
    - Customer notification operations
    - Human review escalation
    - Blocked recovery actions
    """

    idempotency_key = create_idempotency_key(
        record,
        recovery_plan.action,
    )

    executed_at = datetime.now(timezone.utc)

    # --------------------------------------------------
    # GOVERNANCE BLOCKED
    # --------------------------------------------------

    if governance_result.decision == GovernanceDecision.BLOCKED:
        return ExecutionResult(
            record_id=record.record_id,
            action=recovery_plan.action.value,
            status=ExecutionStatus.SKIPPED,
            executed_at=executed_at,
            idempotency_key=idempotency_key,
            detail=(
                "Recovery execution was skipped because "
                f"governance blocked the action: "
                f"{governance_result.message}"
            ),
            recovered_amount=0,
        )

    # --------------------------------------------------
    # HUMAN REVIEW REQUIRED
    # --------------------------------------------------

    if (
        governance_result.decision
        == GovernanceDecision.REQUIRES_REVIEW
    ):
        return ExecutionResult(
            record_id=record.record_id,
            action=recovery_plan.action.value,
            status=ExecutionStatus.REQUIRES_HUMAN_REVIEW,
            executed_at=executed_at,
            idempotency_key=idempotency_key,
            detail=(
                "Recovery execution requires human review: "
                f"{governance_result.message}"
            ),
            recovered_amount=0,
        )

    # --------------------------------------------------
    # APPROVED ACTIONS
    # --------------------------------------------------

    if recovery_plan.action in {
        RecoveryAction.RETRY_PAYMENT,
        RecoveryAction.RETRY_LATER,
    }:
        provider_result = provider.create_retry(
            record_id=record.record_id,
            amount=record.amount,
            idempotency_key=idempotency_key,
        )

        if provider_result.success:
            return ExecutionResult(
                record_id=record.record_id,
                action=recovery_plan.action.value,
                status=ExecutionStatus.SUCCESSFUL,
                executed_at=executed_at,
                idempotency_key=idempotency_key,
                provider_reference=(
                    provider_result.provider_reference
                ),
                detail=provider_result.detail,
                recovered_amount=record.amount,
            )

        return ExecutionResult(
            record_id=record.record_id,
            action=recovery_plan.action.value,
            status=ExecutionStatus.FAILED,
            executed_at=executed_at,
            idempotency_key=idempotency_key,
            provider_reference=(
                provider_result.provider_reference
            ),
            detail=provider_result.detail,
            recovered_amount=0,
        )

    # --------------------------------------------------
    # PAYMENT METHOD UPDATE
    # --------------------------------------------------

    if (
        recovery_plan.action
        == RecoveryAction.REQUEST_PAYMENT_METHOD_UPDATE
    ):
        provider_result = provider.send_notification(
            record_id=record.record_id,
            message=(
                "Your payment method requires updating "
                "before payment recovery can continue."
            ),
        )

        return _create_notification_result(
            record=record,
            action=recovery_plan.action,
            idempotency_key=idempotency_key,
            executed_at=executed_at,
            provider_result=provider_result,
        )

    # --------------------------------------------------
    # MANDATE RENEWAL
    # --------------------------------------------------

    if (
        recovery_plan.action
        == RecoveryAction.REQUEST_MANDATE_RENEWAL
    ):
        provider_result = provider.send_notification(
            record_id=record.record_id,
            message=(
                "Your payment mandate requires renewal "
                "before payment recovery can continue."
            ),
        )

        return _create_notification_result(
            record=record,
            action=recovery_plan.action,
            idempotency_key=idempotency_key,
            executed_at=executed_at,
            provider_result=provider_result,
        )

    # --------------------------------------------------
    # ESCALATE FOR REVIEW
    # --------------------------------------------------

    if (
        recovery_plan.action
        == RecoveryAction.ESCALATE_FOR_REVIEW
    ):
        return ExecutionResult(
            record_id=record.record_id,
            action=recovery_plan.action.value,
            status=ExecutionStatus.REQUIRES_HUMAN_REVIEW,
            executed_at=executed_at,
            idempotency_key=idempotency_key,
            detail=(
                "The recovery action requires human review "
                "and was not automatically executed."
            ),
            recovered_amount=0,
        )

    # --------------------------------------------------
    # STOP RECOVERY
    # --------------------------------------------------

    return ExecutionResult(
        record_id=record.record_id,
        action=recovery_plan.action.value,
        status=ExecutionStatus.SKIPPED,
        executed_at=executed_at,
        idempotency_key=idempotency_key,
        detail=(
            "Recovery execution was skipped because the "
            "recovery plan does not permit further action."
        ),
        recovered_amount=0,
    )


def _create_notification_result(
    record: FailureRecord,
    action: RecoveryAction,
    idempotency_key: str,
    executed_at: datetime,
    provider_result,
) -> ExecutionResult:
    """
    Convert a notification provider response into an ExecutionResult.
    """

    status = (
        ExecutionStatus.SUCCESSFUL
        if provider_result.success
        else ExecutionStatus.FAILED
    )

    return ExecutionResult(
        record_id=record.record_id,
        action=action.value,
        status=status,
        executed_at=executed_at,
        idempotency_key=idempotency_key,
        provider_reference=provider_result.provider_reference,
        detail=provider_result.detail,
        recovered_amount=0,
    )