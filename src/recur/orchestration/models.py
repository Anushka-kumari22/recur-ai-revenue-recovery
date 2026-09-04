from enum import Enum

from pydantic import BaseModel

from recur.diagnosis import DiagnosisResult
from recur.execution.models import ExecutionResult
from recur.governance import GovernanceResult
from recur.models import FailureRecord
from recur.recovery import RecoveryPlan


class PipelineStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineResult(BaseModel):
    """
    Complete result of processing one failed payment through the
    revenue recovery pipeline.
    """

    status: PipelineStatus

    record: FailureRecord

    diagnosis: DiagnosisResult | None = None

    recovery_plan: RecoveryPlan | None = None

    governance_result: GovernanceResult | None = None

    execution_result: ExecutionResult | None = None

    error_message: str | None = None