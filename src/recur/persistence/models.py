from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from recur.persistence.database import Base


class RecoveryAuditRecord(Base):
    """
    Persistent audit record containing the complete result
    of a revenue recovery pipeline execution.
    """

    __tablename__ = "recovery_audit_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    record_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    failure_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    payment_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    customer_contact_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    pipeline_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    pipeline_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    root_cause: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    diagnosis_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    diagnosis_reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    diagnosis_source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    recovery_action: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    expected_recovery_probability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    expected_recovery_value: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    recovery_reasoning: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    governance_decision: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    governance_reason: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    governance_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    execution_status: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    provider_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    execution_detail: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recovered_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )