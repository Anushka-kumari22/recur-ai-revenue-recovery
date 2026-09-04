from recur.diagnosis import diagnose_failure
from recur.execution import (
    PaymentProvider,
    SimulatorProvider,
    execute_recovery_plan,
)
from recur.governance import evaluate_recovery_plan
from recur.models import FailureRecord
from recur.orchestration.models import (
    PipelineResult,
    PipelineStatus,
)
from recur.recovery import create_recovery_plan


def process_failure(
    record: FailureRecord,
    provider: PaymentProvider | None = None,
) -> PipelineResult:
    """
    Process one failed payment through the complete
    revenue recovery pipeline.

    Pipeline flow:

        FailureRecord
            ↓
        Diagnosis
            ↓
        Recovery Planning
            ↓
        Governance
            ↓
        Execution
            ↓
        PipelineResult

    A provider can optionally be supplied for dependency injection.
    When no provider is supplied, the system uses the default
    SimulatorProvider.
    """

    if provider is None:
        provider = SimulatorProvider()

    try:
        diagnosis = diagnose_failure(
            record
        )

        recovery_plan = create_recovery_plan(
            record,
            diagnosis,
        )

        governance_result = evaluate_recovery_plan(
            record,
            recovery_plan,
        )

        execution_result = execute_recovery_plan(
            record,
            recovery_plan,
            governance_result,
            provider,
        )

        return PipelineResult(
            status=PipelineStatus.COMPLETED,
            record=record,
            diagnosis=diagnosis,
            recovery_plan=recovery_plan,
            governance_result=governance_result,
            execution_result=execution_result,
        )

    except Exception as exc:
        return PipelineResult(
            status=PipelineStatus.FAILED,
            record=record,
            error_message=str(exc),
        )