import csv

import pytest

from recur.ingestion import (
    DatasetValidationError,
    load_failure_records,
)


def test_load_failure_records_from_real_dataset():
    records = load_failure_records(
        "data/raw/failed_payments.csv"
    )

    assert len(records) == 150

    first_record = records[0]

    assert first_record.record_id
    assert first_record.customer_id
    assert first_record.amount > 0


def test_missing_file_is_rejected():
    with pytest.raises(FileNotFoundError):
        load_failure_records(
            "data/raw/does_not_exist.csv"
        )


def test_missing_required_columns_are_rejected(tmp_path):
    csv_path = tmp_path / "invalid.csv"

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["record_id", "customer_id"])
        writer.writerow(["rec_001", "cust_001"])

    with pytest.raises(DatasetValidationError):
        load_failure_records(csv_path)