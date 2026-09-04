"""Application service for processing failures and reading analytics."""
from __future__ import annotations

from sqlalchemy.orm import Session

from recur.analytics import get_analytics_dashboard
from recur.exceptions import PipelineProcessingError
from recur.execution import PaymentProvider
from recur.models import FailureRecord
from recur.orchestration import process_failure
from recur.persistence.repository import save_pipeline_result


class RecoveryService:
    def __init__(self, db: Session, provider: PaymentProvider):
        self._db = db
        self._provider = provider

    def process_single_failure(self, record: FailureRecord):
        try:
            result = process_failure(record, provider=self._provider)
        except Exception as exc:
            raise PipelineProcessingError(
                f"Pipeline processing failed for record {record.record_id}."
            ) from exc

        try:
            save_pipeline_result(result, session=self._db)
        except Exception as exc:
            raise PipelineProcessingError(
                f"Pipeline succeeded but persistence failed for record "
                f"{record.record_id}."
            ) from exc

        return result

    def get_analytics_dashboard(self):
        return get_analytics_dashboard(session=self._db)