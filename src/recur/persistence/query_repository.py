from sqlalchemy import select
from sqlalchemy.orm import Session

from recur.persistence.database import SessionLocal
from recur.persistence.models import RecoveryAuditRecord


def get_recovery_records(
    page: int = 1,
    page_size: int = 20,
    customer_id: str | None = None,
    pipeline_status: str | None = None,
) -> tuple[list[RecoveryAuditRecord], int]:
    """
    Retrieve persisted recovery records with optional filters
    and pagination.

    Returns:

        records:
            List of recovery audit records.

        total_records:
            Total number of records matching the filters.
    """

    offset = (
        page - 1
    ) * page_size

    with SessionLocal() as session:

        query = select(
            RecoveryAuditRecord
        )

        if customer_id is not None:

            query = query.where(
                RecoveryAuditRecord.customer_id
                == customer_id
            )

        if pipeline_status is not None:

            query = query.where(
                RecoveryAuditRecord.pipeline_status
                == pipeline_status
            )

        total_records = len(
            session.scalars(
                query
            ).all()
        )

        records = session.scalars(
            query
            .order_by(
                RecoveryAuditRecord.created_at.desc()
            )
            .offset(offset)
            .limit(page_size)
        ).all()

        return records, total_records


def get_recovery_record_by_record_id(
    record_id: str,
) -> RecoveryAuditRecord | None:
    """
    Retrieve the most recent recovery audit record associated
    with a specific payment failure record ID.
    """

    with SessionLocal() as session:

        statement = (
            select(
                RecoveryAuditRecord
            )
            .where(
                RecoveryAuditRecord.record_id
                == record_id
            )
            .order_by(
                RecoveryAuditRecord.created_at.desc()
            )
        )

        return session.scalars(
            statement
        ).first()