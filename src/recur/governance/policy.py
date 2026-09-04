from recur.models import FailureRecord, PaymentStatus
from recur.recovery import RecoveryAction, RecoveryPlan

from recur.governance.models import (
    GovernanceDecision,
    GovernanceReason,
    GovernanceResult,
)


MAX_RETRY_ATTEMPTS = 3
MAX_CUSTOMER_CONTACTS = 3


def evaluate_recovery_plan(
    record: FailureRecord,
    plan: RecoveryPlan,
) -> GovernanceResult:
    """
    Evaluate whether a recovery plan is allowed to proceed.

    Governance rules are evaluated before any action reaches the
    execution layer.
    """

    if record.status != PaymentStatus.FAILED:
        return GovernanceResult(
            decision=GovernanceDecision.BLOCKED,
            reason=GovernanceReason.PAYMENT_NOT_FAILED,
            message=(
                "Recovery is blocked because the payment is not "
                "currently in a failed state."
            ),
        )

    if plan.action == RecoveryAction.STOP_RECOVERY:
        return GovernanceResult(
            decision=GovernanceDecision.BLOCKED,
            reason=GovernanceReason.RECOVERY_STOPPED,
            message=(
                "Recovery is blocked because the recovery planner "
                "recommended stopping further recovery attempts."
            ),
        )

    if (
        plan.action
        in {
            RecoveryAction.RETRY_PAYMENT,
            RecoveryAction.RETRY_LATER,
        }
        and record.attempt_number >= MAX_RETRY_ATTEMPTS
    ):
        return GovernanceResult(
            decision=GovernanceDecision.BLOCKED,
            reason=GovernanceReason.RETRY_LIMIT_EXCEEDED,
            message=(
                "Recovery is blocked because the maximum retry "
                "attempt limit has been reached."
            ),
        )

    if (
        plan.action
        in {
            RecoveryAction.REQUEST_PAYMENT_METHOD_UPDATE,
            RecoveryAction.REQUEST_MANDATE_RENEWAL,
        }
        and record.customer_contact_count
        >= MAX_CUSTOMER_CONTACTS
    ):
        return GovernanceResult(
            decision=GovernanceDecision.BLOCKED,
            reason=GovernanceReason.CONTACT_LIMIT_EXCEEDED,
            message=(
                "Recovery is blocked because the maximum customer "
                "contact limit has been reached."
            ),
        )

    if plan.action == RecoveryAction.ESCALATE_FOR_REVIEW:
        return GovernanceResult(
            decision=GovernanceDecision.REQUIRES_REVIEW,
            reason=GovernanceReason.RISK_REVIEW_REQUIRED,
            message=(
                "The recovery action requires human review before "
                "any further action is taken."
            ),
        )

    return GovernanceResult(
        decision=GovernanceDecision.APPROVED,
        reason=GovernanceReason.ACTION_APPROVED,
        message=(
            "The recovery plan passed all configured governance "
            "checks and is approved to proceed."
        ),
    )