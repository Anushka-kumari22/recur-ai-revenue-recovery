from pathlib import Path
from typing import Any

import pandas as pd

from recur.batch import process_failure_records
from recur.ingestion import load_failure_records
from recur.persistence import (
    create_database_tables,
    save_batch_processing_result,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "failed_payments.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "recovery_results.csv"
)


def pipeline_result_to_row(
    result,
) -> dict[str, Any]:
    """
    Convert a PipelineResult into a flat dictionary suitable
    for CSV storage.

    Each row preserves the complete processing lifecycle of a
    failed payment:

        Failure Record
        → Diagnosis
        → Recovery Plan
        → Governance Decision
        → Execution Result
    """

    row: dict[str, Any] = {
        "record_id": result.record.record_id,
        "customer_id": result.record.customer_id,
        "subscription_id": result.record.subscription_id,
        "amount": str(result.record.amount),
        "currency": result.record.currency,
        "failure_type": result.record.failure_type.value,
        "payment_method": result.record.payment_method.value,
        "attempt_number": result.record.attempt_number,
        "customer_contact_count": (
            result.record.customer_contact_count
        ),
        "pipeline_status": result.status.value,
        "pipeline_error": result.error_message,
    }

    diagnosis = result.diagnosis

    if diagnosis is not None:
        row.update(
            {
                "root_cause": diagnosis.root_cause.value,
                "diagnosis_confidence": diagnosis.confidence,
                "diagnosis_reasoning": diagnosis.reasoning,
                "diagnosis_source": diagnosis.source.value,
            }
        )

    recovery_plan = result.recovery_plan

    if recovery_plan is not None:
        row.update(
            {
                "recovery_action": (
                    recovery_plan.action.value
                ),
                "scheduled_for": (
                    recovery_plan.scheduled_for.isoformat()
                    if recovery_plan.scheduled_for is not None
                    else None
                ),
                "expected_recovery_probability": (
                    recovery_plan.expected_recovery_probability
                ),
                "expected_recovery_value": str(
                    recovery_plan.expected_recovery_value
                ),
                "recovery_reasoning": (
                    recovery_plan.reasoning
                ),
            }
        )

    governance_result = result.governance_result

    if governance_result is not None:
        row.update(
            {
                "governance_decision": (
                    governance_result.decision.value
                ),
                "governance_reason": (
                    governance_result.reason.value
                ),
                "governance_message": (
                    governance_result.message
                ),
            }
        )

    execution_result = result.execution_result

    if execution_result is not None:
        row.update(
            {
                "execution_status": (
                    execution_result.status.value
                ),
                "executed_at": (
                    execution_result.executed_at.isoformat()
                ),
                "idempotency_key": (
                    execution_result.idempotency_key
                ),
                "provider_reference": (
                    execution_result.provider_reference
                ),
                "execution_detail": (
                    execution_result.detail
                ),
                "recovered_amount": str(
                    execution_result.recovered_amount
                ),
            }
        )

    return row


def main() -> None:
    """
    Execute the complete revenue recovery batch pipeline.

    The batch process:

        1. Loads failed payment records.
        2. Processes every record through the recovery pipeline.
        3. Includes diagnosis, planning, governance, and execution.
        4. Persists pipeline audit records to SQLite.
        5. Flattens pipeline results for analytics.
        6. Stores the output as a CSV dataset.
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_FILE}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 60)
    print("RECUR AI REVENUE RECOVERY - BATCH PROCESSING")
    print("=" * 60)

    print(f"\nLoading dataset: {INPUT_FILE}")

    records = load_failure_records(
        INPUT_FILE
    )

    print(f"Loaded records: {len(records)}")

    print("\nProcessing recovery pipeline...")

    batch_result = process_failure_records(
        records
    )

    # --------------------------------------------------
    # DATABASE PERSISTENCE
    # --------------------------------------------------

    print("\nPreparing audit database...")

    create_database_tables()

    print("Saving pipeline audit records...")

    saved_audit_records = save_batch_processing_result(
        batch_result
    )

    print(
        f"Audit records saved: "
        f"{len(saved_audit_records)}"
    )

    # --------------------------------------------------
    # CSV REPORTING
    # --------------------------------------------------

    print("\nGenerating CSV report...")

    output_rows = [
        pipeline_result_to_row(result)
        for result in batch_result.results
    ]

    dataframe = pd.DataFrame(
        output_rows
    )

    dataframe.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)

    print(
        f"Total records: "
        f"{batch_result.total_records}"
    )

    print(
        f"Completed records: "
        f"{batch_result.completed_records}"
    )

    print(
        f"Blocked records: "
        f"{batch_result.blocked_records}"
    )

    print(
        f"Records requiring review: "
        f"{batch_result.records_requiring_review}"
    )

    print(
        f"Processing errors: "
        f"{batch_result.failed_records}"
    )

    print(
        f"Total amount at risk: "
        f"₹{batch_result.total_amount_at_risk}"
    )

    print(
        f"Expected recovery value: "
        f"₹{batch_result.total_expected_recovery_value}"
    )

    # Calculate recovered amount safely without relying
    # on pandas converting Decimal/string values implicitly.
    total_recovered_amount = sum(
        float(
            result.execution_result.recovered_amount
        )
        for result in batch_result.results
        if result.execution_result is not None
    )

    print(
        f"Total simulated recovered amount: "
        f"₹{total_recovered_amount:.2f}"
    )

    print(
        f"\nCSV output file created: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Pipeline audit records stored in SQLite: "
        f"{len(saved_audit_records)}"
    )


if __name__ == "__main__":
    main()