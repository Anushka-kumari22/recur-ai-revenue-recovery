from decimal import Decimal

import pytest

from recur.diagnosis import diagnose_failure
from recur.models import FailureRecord
from recur.recovery import (
    RecoveryAction,
    calculate_expected_recovery_value,
    create_recovery_plan,
)


@pytest.mark.parametrize(
    ("failure_type", "expected_action"),
    [
        (
            "network_timeout",
            RecoveryAction.RETRY_PAYMENT,
        ),
        (
            "insufficient_funds",
            RecoveryAction.RETRY_LATER,
        ),
        (
            "card_expired",
            RecoveryAction.REQUEST_PAYMENT_METHOD_UPDATE,
        ),
        (
            "mandate_expired",
            RecoveryAction.REQUEST_MANDATE_RENEWAL,
        ),
        (
            "bank_decline",
            RecoveryAction.RETRY_LATER,
        ),
        (
            "risk_hold",
            RecoveryAction.ESCALATE_FOR_REVIEW,
        ),
    ],
)
def test_recovery_action_selection(
    failure_type,
    expected_action,
):
    record = FailureRecord(
        record_id="rec_001",
        customer_id="cust_001",
        subscription_id="sub_001",
        amount="1500.00",
        failure_type=failure_type,
        payment_method="upi",
    )

    diagnosis = diagnose_failure(record)

    plan = create_recovery_plan(
        record,
        diagnosis,
    )

    assert plan.action == expected_action


def test_network_timeout_has_retry_schedule():
    record = FailureRecord(
        record_id="rec_001",
        customer_id="cust_001",
        subscription_id="sub_001",
        amount="1000.00",
        failure_type="network_timeout",
        payment_method="upi",
    )

    diagnosis = diagnose_failure(record)
    plan = create_recovery_plan(record, diagnosis)

    assert plan.scheduled_for is not None
    assert plan.expected_recovery_probability > 0


def test_expected_recovery_value():
    value = calculate_expected_recovery_value(
        Decimal("1000.00"),
        Decimal("0.80"),
    )

    assert value == Decimal("800.00")


def test_risk_hold_has_no_expected_recovery_value():
    record = FailureRecord(
        record_id="rec_001",
        customer_id="cust_001",
        subscription_id="sub_001",
        amount="5000.00",
        failure_type="risk_hold",
        payment_method="card",
    )

    diagnosis = diagnose_failure(record)
    plan = create_recovery_plan(record, diagnosis)

    assert plan.action == RecoveryAction.ESCALATE_FOR_REVIEW
    assert plan.expected_recovery_value == Decimal("0.00")