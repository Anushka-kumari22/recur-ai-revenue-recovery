from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from recur.exceptions import PersistenceError
from recur.orchestration import PipelineResult
from recur.persistence.database import SessionLocal
from recur.persistence.models import RecoveryAuditRecord


def save_pipeline_result(
    result: PipelineResult,
) -> RecoveryAuditRecord:
    """
    Persist one complete pipeline result to the audit database.
    """

    record = result.record
    diagnosis = result.diagnosis
    recovery_plan = result.recovery_plan
    governance_result = result.governance_result
    execution_result = result.execution_result

    try:
        audit_record = RecoveryAuditRecord(
            record_id=record.record_id,
            customer_id=record.customer_id,
            subscription_id=record.subscription_id,
            amount=record.amount,
            currency=record.currency,
            failure_type=record.failure_type.value,
            payment_method=record.payment_method.value,
            attempt_number=record.attempt_number,
            customer_contact_count=(
                record.customer_contact_count
            ),
            pipeline_status=result.status.value,
            pipeline_error=result.error_message,

            root_cause=(
                diagnosis.root_cause.value
                if diagnosis is not None
                else None
            ),

            diagnosis_confidence=(
                diagnosis.confidence
                if diagnosis is not None
                else None
            ),

            diagnosis_reasoning=(
                diagnosis.reasoning
                if diagnosis is not None
                else None
            ),

            diagnosis_source=(
                diagnosis.source.value
                if diagnosis is not None
                else None
            ),

            recovery_action=(
                recovery_plan.action.value
                if recovery_plan is not None
                else None
            ),

            expected_recovery_probability=(
                recovery_plan.expected_recovery_probability
                if recovery_plan is not None
                else None
            ),

            expected_recovery_value=(
                recovery_plan.expected_recovery_value
                if recovery_plan is not None
                else None
            ),

            recovery_reasoning=(
                recovery_plan.reasoning
                if recovery_plan is not None
                else None
            ),

            governance_decision=(
                governance_result.decision.value
                if governance_result is not None
                else None
            ),

            governance_reason=(
                governance_result.reason.value
                if governance_result is not None
                else None
            ),

            governance_message=(
                governance_result.message
                if governance_result is not None
                else None
            ),

            execution_status=(
                execution_result.status.value
                if execution_result is not None
                else None
            ),

            idempotency_key=(
                execution_result.idempotency_key
                if execution_result is not None
                else None
            ),

            provider_reference=(
                execution_result.provider_reference
                if execution_result is not None
                else None
            ),

            execution_detail=(
                execution_result.detail
                if execution_result is not None
                else None
            ),

            recovered_amount=(
                execution_result.recovered_amount
                if execution_result is not None
                else Decimal("0")
            ),
        )

        with SessionLocal() as session:
            session.add(audit_record)
            session.commit()
            session.refresh(audit_record)

            return audit_record

    except SQLAlchemyError as exc:
        raise PersistenceError(
            "Failed to save the pipeline result."
        ) from exc