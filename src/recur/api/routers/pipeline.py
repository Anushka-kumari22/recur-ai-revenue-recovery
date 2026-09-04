from fastapi import APIRouter, Depends

from recur.api.dependencies import get_recovery_service
from recur.api.schemas import (
    DiagnosisResponse,
    ExecutionResponse,
    FailureRecordRequest,
    GovernanceResponse,
    PipelineResponse,
    RecoveryPlanResponse,
)
from recur.models import FailureRecord
from recur.services import RecoveryService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def to_pipeline_response(result) -> PipelineResponse:
    diagnosis = None
    if result.diagnosis is not None:
        diagnosis = DiagnosisResponse(
            root_cause=result.diagnosis.root_cause.value,
            confidence=result.diagnosis.confidence,
            reasoning=result.diagnosis.reasoning,
            source=result.diagnosis.source.value,
        )

    recovery_plan = None
    if result.recovery_plan is not None:
        recovery_plan = RecoveryPlanResponse(
            action=result.recovery_plan.action.value,
            expected_recovery_probability=(
                result.recovery_plan.expected_recovery_probability
            ),
            expected_recovery_value=result.recovery_plan.expected_recovery_value,
            scheduled_for=result.recovery_plan.scheduled_for,
            reasoning=result.recovery_plan.reasoning,
        )

    governance = None
    if result.governance_result is not None:
        governance = GovernanceResponse(
            decision=result.governance_result.decision.value,
            reason=result.governance_result.reason.value,
            message=result.governance_result.message,
        )

    execution = None
    if result.execution_result is not None:
        execution = ExecutionResponse(
            status=result.execution_result.status.value,
            detail=result.execution_result.detail,
            provider_reference=result.execution_result.provider_reference,
            recovered_amount=result.execution_result.recovered_amount,
        )

    return PipelineResponse(
        record_id=result.record.record_id,
        pipeline_status=result.status.value,
        diagnosis=diagnosis,
        recovery_plan=recovery_plan,
        governance=governance,
        execution=execution,
        error_message=result.error_message,
    )


@router.post("/process", response_model=PipelineResponse)
def process_payment(
    request: FailureRecordRequest,
    service: RecoveryService = Depends(get_recovery_service),
) -> PipelineResponse:
    record = FailureRecord(**request.model_dump())
    return to_pipeline_response(service.process_single_failure(record))
