from recur.diagnosis.models import (
    DiagnosisResult,
    DiagnosisSource,
    RootCause,
)
from recur.models import (
    FailureRecord,
    FailureType,
    MandateStatus,
)


def diagnose_failure(record: FailureRecord) -> DiagnosisResult:
    """
    Diagnose a payment failure using deterministic business rules.

    Rules are explicit and explainable. Later, ambiguous cases can be
    escalated to an LLM without changing the DiagnosisResult contract.
    """

    if record.failure_type == FailureType.NETWORK_TIMEOUT:
        return DiagnosisResult(
            root_cause=RootCause.TEMPORARY_TECHNICAL_ISSUE,
            confidence=0.95,
            source=DiagnosisSource.RULE_BASED,
            reasoning="The payment failed because of a network timeout, "
            "which is typically a temporary technical issue.",
        )

    if record.failure_type == FailureType.INSUFFICIENT_FUNDS:
        return DiagnosisResult(
            root_cause=RootCause.INSUFFICIENT_FUNDS,
            confidence=0.98,
            source=DiagnosisSource.RULE_BASED,
            reasoning="The failure signal explicitly indicates insufficient funds.",
        )

    if record.failure_type == FailureType.CARD_EXPIRED:
        return DiagnosisResult(
            root_cause=RootCause.PAYMENT_INSTRUMENT_EXPIRED,
            confidence=0.98,
            source=DiagnosisSource.RULE_BASED,
            reasoning="The payment instrument is reported as expired.",
        )

    if (
        record.failure_type == FailureType.MANDATE_EXPIRED
        or record.mandate_status == MandateStatus.EXPIRED
    ):
        return DiagnosisResult(
            root_cause=RootCause.MANDATE_ISSUE,
            confidence=0.99,
            source=DiagnosisSource.RULE_BASED,
            reasoning="The subscription mandate is expired and requires renewal.",
        )

    if record.failure_type == FailureType.BANK_DECLINE:
        return DiagnosisResult(
            root_cause=RootCause.BANK_DECLINE,
            confidence=0.85,
            source=DiagnosisSource.RULE_BASED,
            reasoning="The payment was declined by the banking system.",
        )

    if record.failure_type == FailureType.RISK_HOLD:
        return DiagnosisResult(
            root_cause=RootCause.RISK_REVIEW_REQUIRED,
            confidence=0.95,
            source=DiagnosisSource.RULE_BASED,
            reasoning="The payment is under a risk hold and should not be retried automatically.",
        )

    return DiagnosisResult(
        root_cause=RootCause.UNKNOWN,
        confidence=0.0,
        source=DiagnosisSource.RULE_BASED,
        reasoning="No deterministic diagnosis rule matched this failure.",
    )