from recur.models import FailureRecord
from recur.recovery import RecoveryAction


def create_idempotency_key(
    record: FailureRecord,
    action: RecoveryAction,
) -> str:
    """
    Create a deterministic idempotency key for a recovery action.

    The same record, attempt number, and action will always produce
    the same key. This allows the execution layer to detect duplicate
    execution attempts.
    """

    return (
        f"{record.record_id}:"
        f"{record.attempt_number}:"
        f"{action.value}"
    )