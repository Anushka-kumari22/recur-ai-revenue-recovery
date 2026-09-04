import pytest

from recur.diagnosis import RootCause, diagnose_failure
from recur.models import FailureRecord


@pytest.mark.parametrize(
    ("failure_type", "expected_cause"),
    [
        ("network_timeout", RootCause.TEMPORARY_TECHNICAL_ISSUE),
        ("insufficient_funds", RootCause.INSUFFICIENT_FUNDS),
        ("card_expired", RootCause.PAYMENT_INSTRUMENT_EXPIRED),
        ("mandate_expired", RootCause.MANDATE_ISSUE),
        ("bank_decline", RootCause.BANK_DECLINE),
        ("risk_hold", RootCause.RISK_REVIEW_REQUIRED),
    ],
)
def test_known_failure_types_are_diagnosed(
    failure_type,
    expected_cause,
):
    record = FailureRecord(
        record_id="rec_001",
        customer_id="cust_001",
        subscription_id="sub_001",
        amount="1500",
        failure_type=failure_type,
        payment_method="upi",
    )

    result = diagnose_failure(record)

    assert result.root_cause == expected_cause
    assert result.confidence > 0


def test_expired_mandate_is_detected():
    record = FailureRecord(
        record_id="rec_001",
        customer_id="cust_001",
        subscription_id="sub_001",
        amount="1500",
        failure_type="bank_decline",
        payment_method="upi",
        mandate_status="expired",
    )

    result = diagnose_failure(record)

    assert result.root_cause == RootCause.MANDATE_ISSUE