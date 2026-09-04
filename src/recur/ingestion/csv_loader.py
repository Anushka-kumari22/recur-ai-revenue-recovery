from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ValidationError

from recur.models import FailureRecord


REQUIRED_COLUMNS = {
    "record_id",
    "customer_id",
    "amount",
    "currency",
    "failure_type",
    "payment_method",
    "attempt_number",
    "subscription_id",
    "mandate_status",
    "customer_contact_count",
    "failed_at",
    "days_since_failure",
}


class DatasetValidationError(ValueError):
    """Raised when the payment dataset has an invalid structure."""


def validate_csv_columns(fieldnames: list[str] | None) -> None:
    """Validate that all required columns exist in the CSV file."""

    if not fieldnames:
        raise DatasetValidationError(
            "The CSV file does not contain a valid header."
        )

    missing_columns = REQUIRED_COLUMNS - set(fieldnames)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))

        raise DatasetValidationError(
            f"Dataset is missing required columns: {missing}"
        )


def load_failure_records(
    csv_path: str | Path,
) -> list[FailureRecord]:
    """
    Load failed-payment records from a CSV file.

    Each row is validated against the application's canonical
    FailureRecord model.
    """

    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file was not found: {path}"
        )

    if not path.is_file():
        raise DatasetValidationError(
            f"Dataset path is not a file: {path}"
        )

    records: list[FailureRecord] = []

    with path.open(
        mode="r",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        validate_csv_columns(reader.fieldnames)

        for row_number, row in enumerate(reader, start=2):
            try:
                record = FailureRecord.model_validate(row)
                records.append(record)

            except ValidationError as error:
                raise DatasetValidationError(
                    f"Invalid data at CSV row {row_number}: {error}"
                ) from error

    return records