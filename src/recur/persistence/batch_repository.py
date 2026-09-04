from recur.batch import BatchProcessingResult
from recur.persistence.models import RecoveryAuditRecord
from recur.persistence.repository import save_pipeline_result


def save_batch_processing_result(
    batch_result: BatchProcessingResult,
) -> list[RecoveryAuditRecord]:
    """
    Persist every pipeline result produced during a batch operation.

    Each PipelineResult is stored as an independent audit record.

    If a single record fails to persist, the exception is propagated so
    the caller can explicitly decide how database persistence failures
    should be handled.
    """

    saved_records: list[RecoveryAuditRecord] = []

    for result in batch_result.results:
        audit_record = save_pipeline_result(result)
        saved_records.append(audit_record)

    return saved_records