import pytest
from fastapi.testclient import TestClient

from recur.api.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

def create_valid_payload() -> dict:
    """
    Return a valid failed payment payload for API testing.
    """

    return {
        "record_id": "api_test_record_001",
        "customer_id": "api_test_customer_001",
        "subscription_id": "api_test_subscription_001",
        "amount": "1500.00",
        "currency": "INR",
        "failure_type": "network_timeout",
        "payment_method": "upi",
        "attempt_number": 0,
        "customer_contact_count": 0,
    }


# --------------------------------------------------
# HEALTH CHECK TESTS
# --------------------------------------------------


def test_health_endpoint_returns_healthy_status(client):
    """
    Verify that the health endpoint confirms that the API
    is running.
    """

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"

    assert (
        data["service"]
        == "recur-ai-revenue-recovery"
    )


# --------------------------------------------------
# ANALYTICS TESTS
# --------------------------------------------------


def test_analytics_dashboard_returns_successfully(client):
    """
    Verify that the analytics dashboard endpoint is
    accessible and returns data.
    """

    response = client.get(
        "/analytics/dashboard"
    )

    assert response.status_code == 200

    data = response.json()

    assert data is not None


# --------------------------------------------------
# PIPELINE SUCCESS TEST
# --------------------------------------------------


def test_process_failure_successfully(client):
    """
    Verify that a valid failed payment completes the
    full recovery pipeline.
    """

    payload = create_valid_payload()

    response = client.post(
        "/pipeline/process",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"

    assert (
        data["record"]["record_id"]
        == payload["record_id"]
    )

    assert (
        data["diagnosis"]["root_cause"]
        == "temporary_technical_issue"
    )

    assert (
        data["recovery_plan"]["action"]
        == "retry_payment"
    )

    assert (
        data["governance_result"]["decision"]
        == "approved"
    )

    assert (
        data["execution_result"]["status"]
        == "successful"
    )

    assert (
        data["execution_result"]["recovered_amount"]
        == "1500.00"
    )


# --------------------------------------------------
# REQUEST VALIDATION TESTS
# --------------------------------------------------


def test_negative_payment_amount_is_rejected(client):
    """
    Verify that negative payment amounts are rejected
    by the API validation layer.
    """

    payload = create_valid_payload()

    payload["amount"] = "-100.00"

    response = client.post(
        "/pipeline/process",
        json=payload,
    )

    assert response.status_code == 422


def test_zero_payment_amount_is_rejected(client):
    """
    Verify that zero payment amounts are rejected.
    """

    payload = create_valid_payload()

    payload["amount"] = "0"

    response = client.post(
        "/pipeline/process",
        json=payload,
    )

    assert response.status_code == 422


def test_empty_record_id_is_rejected(client):
    """
    Verify that an empty record ID is rejected.
    """

    payload = create_valid_payload()

    payload["record_id"] = ""

    response = client.post(
        "/pipeline/process",
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_failure_type_is_rejected(client):
    """
    Verify that unsupported failure types are rejected.
    """

    payload = create_valid_payload()

    payload["failure_type"] = "invalid_failure"

    response = client.post(
        "/pipeline/process",
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_payment_method_is_rejected(client):
    """
    Verify that unsupported payment methods are rejected.
    """

    payload = create_valid_payload()

    payload["payment_method"] = "invalid_payment_method"

    response = client.post(
        "/pipeline/process",
        json=payload,
    )

    assert response.status_code == 422


def test_negative_attempt_number_is_rejected(client):
    """
    Verify that negative attempt numbers are rejected.
    """

    payload = create_valid_payload()

    payload["attempt_number"] = -1

    response = client.post(
        "/pipeline/process",
        json=payload,
    )

    assert response.status_code == 422


def test_negative_contact_count_is_rejected(client):
    """
    Verify that negative customer contact counts are
    rejected.
    """

    payload = create_valid_payload()

    payload["customer_contact_count"] = -1

    response = client.post(
        "/pipeline/process",
        json=payload,
    )

    assert response.status_code == 422