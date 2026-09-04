from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from recur.diagnosis import (
    DiagnosisResult,
    DiagnosisSource,
    RootCause,
)
from recur.execution.models import (
    ExecutionResult,
    ExecutionStatus,
)
from recur.governance import (
    GovernanceDecision,
    GovernanceReason,
    GovernanceResult,
)
from recur.models import (
    FailureRecord,
    FailureType,
    MandateStatus,
    PaymentMethod,
    PaymentStatus,
)
from recur.orchestration import (
    PipelineResult,
    PipelineStatus,
)
from recur.persistence.database import Base
from recur.persistence.models import RecoveryAuditRecord
from recur.persistence.repository import save_pipeline_result
from recur.recovery import (
    RecoveryAction,
    RecoveryPlan,
)


def create_test_session():
    """
    Create an isolated in-memory database session.

    This prevents unit tests from modifying the real recur.db file.
    """

    engine = create_engine(
        "sqlite:///:memory:"
    )

    Base.metadata.create_all(
        bind=engine
    )

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    return session_factory()


def create_record():
    return FailureRecord(
        record_id="record_001",
        customer_id="customer_001",
        subscription_id="subscription_001",
        amount=Decimal("1500.00"),
        currency="INR",
        failure_type=FailureType.NETWORK_TIMEOUT,
        payment_method=PaymentMethod.UPI,
        attempt_number=0,
        mandate_status=MandateStatus.ACTIVE,
        customer_contact_count=0,
        failed_at=datetime.now(timezone.utc),
        days_since_failure=0,
        status=PaymentStatus.FAILED,
    )


def create_diagnosis():
    return DiagnosisResult(
        root_cause=RootCause.TEMPORARY_TECHNICAL_ISSUE,
        confidence=0.90,
        reasoning="Test diagnosis.",
        source=DiagnosisSource.RULE_BASED,
    )


def create_recovery_plan():
    return RecoveryPlan(
        action=RecoveryAction.RETRY_PAYMENT,
        diagnosis=create_diagnosis(),
        confidence=0.90,
        scheduled_for=None,
        expected_recovery_probability=0.80,
        expected_recovery_value=Decimal("1200.00"),
        reasoning="Test recovery plan.",
    )


def create_governance_result():
    return GovernanceResult(
        decision=GovernanceDecision.APPROVED,
        reason=GovernanceReason.ACTION_APPROVED,
        message="Recovery plan approved.",
    )


def create_execution_result():
    return ExecutionResult(
        record_id="record_001",
        action=RecoveryAction.RETRY_PAYMENT.value,
        status=ExecutionStatus.SUCCESSFUL,
        executed_at=datetime.now(timezone.utc),
        idempotency_key=(
            "record_001:0:retry_payment"
        ),
        provider_reference="sim_ref_001",
        detail="Simulated payment retry succeeded.",
        recovered_amount=Decimal("1500.00"),
    )


def create_pipeline_result():
    return PipelineResult(
        status=PipelineStatus.COMPLETED,
        record=create_record(),
        diagnosis=create_diagnosis(),
        recovery_plan=create_recovery_plan(),
        governance_result=create_governance_result(),
        execution_result=create_execution_result(),
    )


def test_audit_record_model_can_be_created():

    session = create_test_session()

    audit_record = RecoveryAuditRecord(
        record_id="record_001",
        customer_id="customer_001",
        subscription_id="subscription_001",
        amount=Decimal("1500.00"),
        currency="INR",
        failure_type="network_timeout",
        payment_method="upi",
        attempt_number=0,
        customer_contact_count=0,
        pipeline_status="completed",
    )

    session.add(audit_record)

    session.commit()

    assert audit_record.id is not None

    session.close()


def test_pipeline_result_is_saved(monkeypatch):

    session = create_test_session()

    def test_session_local():
        return session

    monkeypatch.setattr(
        "recur.persistence.repository.SessionLocal",
        test_session_local,
    )

    pipeline_result = create_pipeline_result()

    saved_record = save_pipeline_result(
        pipeline_result
    )

    assert saved_record.id is not None

    assert (
        saved_record.record_id
        == "record_001"
    )

    assert (
        saved_record.pipeline_status
        == "completed"
    )

    assert (
        saved_record.root_cause
        == "temporary_technical_issue"
    )

    assert (
        saved_record.recovery_action
        == "retry_payment"
    )

    assert (
        saved_record.governance_decision
        == "approved"
    )

    assert (
        saved_record.execution_status
        == "successful"
    )

    assert (
        saved_record.idempotency_key
        == "record_001:0:retry_payment"
    )

    assert (
        saved_record.recovered_amount
        == Decimal("1500.00")
    )


def test_saved_record_can_be_retrieved(monkeypatch):

    session = create_test_session()

    def test_session_local():
        return session

    monkeypatch.setattr(
        "recur.persistence.repository.SessionLocal",
        test_session_local,
    )

    pipeline_result = create_pipeline_result()

    saved_record = save_pipeline_result(
        pipeline_result
    )

    retrieved_record = (
        session.query(RecoveryAuditRecord)
        .filter(
            RecoveryAuditRecord.id
            == saved_record.id
        )
        .first()
    )

    assert retrieved_record is not None

    assert (
        retrieved_record.record_id
        == "record_001"
    )

    assert (
        retrieved_record.customer_id
        == "customer_001"
    )

    assert (
        retrieved_record.recovered_amount
        == Decimal("1500.00")
    )