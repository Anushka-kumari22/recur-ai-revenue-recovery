from recur.api.responses import (
    RecoveryListResponse,
    RecoveryRecordResponse,
)

from recur.persistence import (
    get_recovery_record_by_record_id,
    get_recovery_records,
)


def get_recovery_history(
    page: int = 1,
    page_size: int = 20,
    customer_id: str | None = None,
    pipeline_status: str | None = None,
) -> RecoveryListResponse:
    """
    Retrieve paginated recovery history.

    This service acts as an abstraction layer between
    the FastAPI routes and the persistence layer.
    """

    records, total_records = (
        get_recovery_records(
            page=page,
            page_size=page_size,
            customer_id=customer_id,
            pipeline_status=pipeline_status,
        )
    )

    return RecoveryListResponse(
        total_records=total_records,
        page=page,
        page_size=page_size,
        records=[
            RecoveryRecordResponse.model_validate(
                record
            )
            for record in records
        ],
    )


def get_recovery_details(
    record_id: str,
) -> RecoveryRecordResponse | None:
    """
    Retrieve detailed recovery information for one
    failed payment record.
    """

    record = (
        get_recovery_record_by_record_id(
            record_id
        )
    )

    if record is None:
        return None

    return RecoveryRecordResponse.model_validate(
        record
    )