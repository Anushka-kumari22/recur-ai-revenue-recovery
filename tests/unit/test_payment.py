from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from recur.models import (
    FailureRecord,
    FailureType,
    MandateStatus,
    PaymentMethod,
    PaymentStatus,
)


def create_valid_record(**overrides):
    data = {
        "record_id": "rec_001",
        "customer_id": "cust_001",
        "subscription_id": "sub_001",
        "amount": "1500.50",
        "currency": "INR",
        "failure_type": FailureType.NETWORK_TIMEOUT,
        "payment_method": PaymentMethod.UPI,
        "attempt_number": 0,
        "mandate_status": MandateStatus.ACTIVE,
        "customer_contact_count": 0,
        "failed_at": datetime.now(timezone.utc),
        "days_since_failure": 2,
    }

    data.update(overrides)

    return FailureRecord(**data)


def test_failure_record_creation():
    record = create_valid_record()

    assert record.record_id == "rec_001"
    assert record.customer_id == "cust_001"
    assert record.subscription_id == "sub_001"
    assert record.amount == Decimal("1500.50")
    assert record.failure_type == FailureType.NETWORK_TIMEOUT
    assert record.payment_method == PaymentMethod.UPI
    assert record.status == PaymentStatus.FAILED


def test_negative_amount_is_rejected():
    with pytest.raises(ValidationError):
        create_valid_record(amount="-500")


def test_zero_amount_is_rejected():
    with pytest.raises(ValidationError):
        create_valid_record(amount="0")


def test_negative_attempt_number_is_rejected():
    with pytest.raises(ValidationError):
        create_valid_record(attempt_number=-1)


def test_negative_contact_count_is_rejected():
    with pytest.raises(ValidationError):
        create_valid_record(customer_contact_count=-1)


def test_currency_is_normalized():
    record = create_valid_record(currency="inr")

    assert record.currency == "INR"


def test_empty_identifier_is_rejected():
    with pytest.raises(ValidationError):
        create_valid_record(record_id="   ")