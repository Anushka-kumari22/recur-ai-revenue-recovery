from decimal import Decimal

from recur.analytics import get_analytics_dashboard
from recur.persistence import (
    RecoveryAuditRecord,
    SessionLocal,
    create_database_tables,
)


def _clear_audit_records() -> None:
    """
    Remove existing audit records so each analytics test
    starts with a controlled database state.
    """

    with SessionLocal() as session:
        session.query(
            RecoveryAuditRecord
        ).delete()

        session.commit()


def _create_audit_record(
    record_id: str,
    amount: Decimal,
    expected_recovery_value: Decimal,
    recovered_amount: Decimal,
    pipeline_status: str = "completed",
    governance_decision: str = "approved",
    execution_status: str = "successful",
    root_cause: str = "temporary_technical_issue",
    recovery_action: str = "retry_payment",
) -> RecoveryAuditRecord:
    """
    Create a test audit record with sensible defaults.
    """

    return RecoveryAuditRecord(
        record_id=record_id,
        customer_id=f"customer_{record_id}",
        subscription_id=f"subscription_{record_id}",
        amount=amount,
        currency="INR",
        failure_type="network_timeout",
        payment_method="upi",
        attempt_number=0,
        customer_contact_count=0,
        pipeline_status=pipeline_status,
        pipeline_error=None,
        root_cause=root_cause,
        diagnosis_confidence=0.95,
        diagnosis_reasoning="Test diagnosis.",
        diagnosis_source="rule_based",
        recovery_action=recovery_action,
        expected_recovery_probability=0.80,
        expected_recovery_value=expected_recovery_value,
        recovery_reasoning="Test recovery plan.",
        governance_decision=governance_decision,
        governance_reason="action_approved",
        governance_message="Test governance decision.",
        execution_status=execution_status,
        idempotency_key=f"{record_id}:0:{recovery_action}",
        provider_reference=f"provider_{record_id}",
        execution_detail="Test execution.",
        recovered_amount=recovered_amount,
    )


def _save_records(
    records: list[RecoveryAuditRecord],
) -> None:
    """
    Save test records into the audit database.
    """

    with SessionLocal() as session:
        session.add_all(records)
        session.commit()


def test_empty_database_returns_zero_metrics():
    """
    Analytics should safely handle an empty database.
    """

    create_database_tables()
    _clear_audit_records()

    dashboard = get_analytics_dashboard()

    assert dashboard.summary.total_records == 0
    assert dashboard.summary.completed_records == 0
    assert (
        dashboard.summary.total_amount_at_risk
        == Decimal("0")
    )
    assert (
        dashboard.summary.total_recovered_amount
        == Decimal("0")
    )
    assert dashboard.summary.recovery_rate == 0.0


def test_analytics_calculates_financial_metrics():
    """
    Verify that financial metrics are aggregated correctly.
    """

    create_database_tables()
    _clear_audit_records()

    records = [
        _create_audit_record(
            record_id="record_001",
            amount=Decimal("1000"),
            expected_recovery_value=Decimal("800"),
            recovered_amount=Decimal("1000"),
        ),
        _create_audit_record(
            record_id="record_002",
            amount=Decimal("500"),
            expected_recovery_value=Decimal("300"),
            recovered_amount=Decimal("0"),
            execution_status="failed",
        ),
    ]

    _save_records(records)

    dashboard = get_analytics_dashboard()

    assert dashboard.summary.total_records == 2

    assert (
        dashboard.summary.total_amount_at_risk
        == Decimal("1500")
    )

    assert (
        dashboard.summary.total_expected_recovery_value
        == Decimal("1100")
    )

    assert (
        dashboard.summary.total_recovered_amount
        == Decimal("1000")
    )

    assert dashboard.summary.recovery_rate == 66.67


def test_analytics_calculates_governance_metrics():
    """
    Verify approved, blocked, and human review counts.
    """

    create_database_tables()
    _clear_audit_records()

    records = [
        _create_audit_record(
            record_id="record_001",
            amount=Decimal("100"),
            expected_recovery_value=Decimal("80"),
            recovered_amount=Decimal("100"),
            governance_decision="approved",
        ),
        _create_audit_record(
            record_id="record_002",
            amount=Decimal("200"),
            expected_recovery_value=Decimal("0"),
            recovered_amount=Decimal("0"),
            governance_decision="blocked",
            execution_status="skipped",
        ),
        _create_audit_record(
            record_id="record_003",
            amount=Decimal("300"),
            expected_recovery_value=Decimal("0"),
            recovered_amount=Decimal("0"),
            governance_decision="requires_review",
            execution_status="requires_human_review",
        ),
    ]

    _save_records(records)

    dashboard = get_analytics_dashboard()

    assert dashboard.summary.approved_actions == 1
    assert dashboard.summary.blocked_actions == 1
    assert (
        dashboard.summary.records_requiring_review
        == 1
    )


def test_analytics_returns_distributions():
    """
    Verify categorical distributions are calculated correctly.
    """

    create_database_tables()
    _clear_audit_records()

    records = [
        _create_audit_record(
            record_id="record_001",
            amount=Decimal("100"),
            expected_recovery_value=Decimal("80"),
            recovered_amount=Decimal("100"),
            root_cause="temporary_technical_issue",
            recovery_action="retry_payment",
        ),
        _create_audit_record(
            record_id="record_002",
            amount=Decimal("200"),
            expected_recovery_value=Decimal("100"),
            recovered_amount=Decimal("0"),
            root_cause="temporary_technical_issue",
            recovery_action="retry_payment",
        ),
        _create_audit_record(
            record_id="record_003",
            amount=Decimal("300"),
            expected_recovery_value=Decimal("150"),
            recovered_amount=Decimal("0"),
            root_cause="insufficient_funds",
            recovery_action="retry_later",
        ),
    ]

    _save_records(records)

    dashboard = get_analytics_dashboard()

    root_causes = {
        item.category: item.count
        for item in dashboard.root_cause_distribution
    }

    recovery_actions = {
        item.category: item.count
        for item in dashboard.recovery_action_distribution
    }

    assert (
        root_causes[
            "temporary_technical_issue"
        ]
        == 2
    )

    assert (
        root_causes[
            "insufficient_funds"
        ]
        == 1
    )

    assert (
        recovery_actions[
            "retry_payment"
        ]
        == 2
    )

    assert (
        recovery_actions[
            "retry_later"
        ]
        == 1
    )