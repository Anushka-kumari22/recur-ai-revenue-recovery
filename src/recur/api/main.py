import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from recur.exceptions import RecurApplicationError
from recur.analytics import get_analytics_dashboard
from recur.api.schemas import FailureRecordRequest
from recur.execution import SimulatorProvider
from recur.logging import configure_logging
from recur.models import FailureRecord
from recur.orchestration import process_failure
from recur.persistence import (
    create_database_tables,
    save_pipeline_result,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize application infrastructure during startup
    and perform cleanup during shutdown.
    """

    configure_logging()

    logger.info(
        "Starting Recur AI Revenue Recovery API"
    )

    create_database_tables()

    logger.info(
        "Database tables initialized successfully"
    )

    yield

    logger.info(
        "Shutting down Recur AI Revenue Recovery API"
    )


app = FastAPI(
    title="Recur AI Revenue Recovery API",
    description=(
        "An intelligent revenue recovery system that "
        "diagnoses failed payments, creates recovery plans, "
        "applies governance rules, executes approved actions, "
        "and provides recovery analytics."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected application exceptions centrally.

    Internal exception details are logged but are not exposed
    directly to API clients.
    """

    logger.exception(
        "Unhandled exception during request "
        "method=%s path=%s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": (
                "An unexpected internal server error occurred."
            ),
        },
    )


@app.get("/health")
def health_check() -> dict:
    """
    Basic API health check.
    """

    logger.debug(
        "Health check requested"
    )

    return {
        "status": "healthy",
        "service": "recur-ai-revenue-recovery",
    }


@app.get("/analytics/dashboard")
def analytics_dashboard():
    """
    Return the complete revenue recovery analytics dashboard.
    """

    logger.info(
        "Analytics dashboard requested"
    )

    return get_analytics_dashboard()


@app.post("/pipeline/process")
def process_payment_failure(
    request: FailureRecordRequest,
):
    """
    Process a single failed payment through the complete
    revenue recovery pipeline.

    Flow:

        Failure
          ↓
        Diagnosis
          ↓
        Recovery Planning
          ↓
        Governance
          ↓
        Execution
          ↓
        Persistence
    """

    logger.info(
        "Processing payment failure record_id=%s",
        request.record_id,
    )

    record = FailureRecord(
        record_id=request.record_id,
        customer_id=request.customer_id,
        subscription_id=request.subscription_id,
        amount=request.amount,
        currency=request.currency,
        failure_type=request.failure_type,
        payment_method=request.payment_method,
        attempt_number=request.attempt_number,
        customer_contact_count=(
            request.customer_contact_count
        ),
    )

    provider = SimulatorProvider()

    result = process_failure(
        record,
        provider=provider,
    )

    logger.info(
        "Pipeline completed "
        "record_id=%s status=%s",
        request.record_id,
        result.status.value,
    )

    save_pipeline_result(
        result,
    )

    logger.info(
        "Pipeline result persisted "
        "record_id=%s",
        request.record_id,
    )

    return result