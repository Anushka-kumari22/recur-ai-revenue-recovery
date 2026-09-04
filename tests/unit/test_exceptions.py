import pytest

from recur.exceptions import (
    PersistenceError,
    PipelineProcessingError,
    RecurApplicationError,
    ResourceNotFoundError,
)


def test_base_application_error():
    error = RecurApplicationError(
        "Application error occurred."
    )

    assert str(error) == (
        "Application error occurred."
    )

    assert error.status_code == 500


def test_resource_not_found_error():
    error = ResourceNotFoundError(
        "Resource not found."
    )

    assert isinstance(
        error,
        RecurApplicationError,
    )

    assert error.status_code == 404


def test_persistence_error():
    error = PersistenceError(
        "Database operation failed."
    )

    assert isinstance(
        error,
        RecurApplicationError,
    )

    assert error.status_code == 500


def test_pipeline_processing_error():
    error = PipelineProcessingError(
        "Pipeline processing failed."
    )

    assert isinstance(
        error,
        RecurApplicationError,
    )

    assert error.status_code == 500