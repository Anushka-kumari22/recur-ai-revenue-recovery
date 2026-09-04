from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class RecoveryRecordResponse(BaseModel):
    """
    API representation of one persisted recovery pipeline
    execution.
    """

    id: int

    record_id: str

    customer_id: str

    subscription_id: str

    amount: Decimal

    currency: str

    failure_type: str

    payment_method: str

    attempt_number: int

    customer_contact_count: int

    pipeline_status: str

    pipeline_error: str | None = None

    root_cause: str | None = None

    diagnosis_confidence: float | None = None

    diagnosis_reasoning: str | None = None

    diagnosis_source: str | None = None

    recovery_action: str | None = None

    expected_recovery_probability: float | None = None

    expected_recovery_value: Decimal | None = None

    recovery_reasoning: str | None = None

    governance_decision: str | None = None

    governance_reason: str | None = None

    governance_message: str | None = None

    execution_status: str | None = None

    idempotency_key: str | None = None

    provider_reference: str | None = None

    execution_detail: str | None = None

    recovered_amount: Decimal | None = None

    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class RecoveryListResponse(BaseModel):
    """
    Paginated response containing recovery records.
    """

    total_records: int

    page: int

    page_size: int

    records: list[RecoveryRecordResponse]