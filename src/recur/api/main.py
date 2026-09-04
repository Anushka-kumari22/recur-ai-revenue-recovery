"""Application entrypoint and compatibility routes."""

import logging
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from recur.analytics import get_analytics_dashboard
from recur.api.responses import (
    RecoveryListResponse,
    RecoveryRecordResponse,
)
from recur.api.routers import (
    analytics,
    health,
    pipeline,
)
from recur.api.schemas import (
    ErrorResponse,
    FailureRecordRequest,
)
from recur.api.services import (
    get_recovery_details,
    get_recovery_history,
)
from recur.exceptions import RecurApplicationError
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
        "Revenue recovery diagnosis, planning, governance, "
        "execution, persistence, and analytics."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
@app.get("/")
def root():
    return {
        "message": "Recur AI Revenue Recovery API is running",
        "status": "healthy",
        "docs": "/docs",
        "health": "/api/v1/health",
    }

# ============================================================
# VERSIONED API ROUTERS
# ============================================================

app.include_router(
    health.router,
    prefix="/api/v1",
)

app.include_router(
    pipeline.router,
    prefix="/api/v1",
)

app.include_router(
    analytics.router,
    prefix="/api/v1",
)


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(RecurApplicationError)
async def application_exception_handler(
    request: Request,
    exc: RecurApplicationError,
) -> JSONResponse:
    """
    Handle known application-specific exceptions.
    """

    logger.warning(
        "Application error method=%s path=%s detail=%s",
        request.method,
        request.url.path,
        str(exc),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=str(exc),
        ).model_dump(mode="json"),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Return a consistent response for request validation
    failures.
    """

    logger.warning(
        "Request validation failed method=%s path=%s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail="Request validation failed.",
            errors=[
                {
                    "error_code": error["type"],
                    "message": error["msg"],
                    "field": ".".join(
                        str(item)
                        for item in error["loc"]
                    ),
                }
                for error in exc.errors()
            ],
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected exceptions centrally.

    Internal exception details are logged but are not
    exposed to API clients.
    """

    logger.exception(
        "Unhandled exception during request "
        "method=%s path=%s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail=(
                "An unexpected internal server error occurred."
            ),
        ).model_dump(mode="json"),
    )


# ============================================================
# RECOVERY HISTORY ENDPOINTS
# ============================================================

@app.get(
    "/recoveries",
    response_model=RecoveryListResponse,
)

def list_recoveries(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number to retrieve.",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of records per page.",
    ),
    customer_id: str | None = Query(
        default=None,
        description="Filter records by customer ID.",
    ),
    pipeline_status: str | None = Query(
        default=None,
        description="Filter records by pipeline status.",
    ),
) -> RecoveryListResponse:
    """
    Retrieve persisted recovery records.

    Supports pagination and optional filtering by
    customer ID and pipeline status.
    """

    logger.info(
        "Recovery history requested "
        "page=%s page_size=%s customer_id=%s "
        "pipeline_status=%s",
        page,
        page_size,
        customer_id,
        pipeline_status,
    )

    return get_recovery_history(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        pipeline_status=pipeline_status,
    )


@app.get(
    "/recoveries/{record_id}",
    response_model=RecoveryRecordResponse,
)
def get_recovery(
    record_id: str,
) -> RecoveryRecordResponse:
    """
    Retrieve the most recent recovery result associated
    with a specific failed payment record.
    """

    logger.info(
        "Recovery details requested record_id=%s",
        record_id,
    )

    recovery = get_recovery_details(
        record_id
    )

    if recovery is None:

        logger.warning(
            "Recovery record not found record_id=%s",
            record_id,
        )

        raise HTTPException(
            status_code=404,
            detail="Recovery record not found.",
        )

    return recovery


# ============================================================
# LEGACY COMPATIBILITY ROUTES
# ============================================================

@app.get("/health")
def legacy_health() -> dict:
    """
    Legacy health endpoint.

    The versioned endpoint is available through
    /api/v1/health.
    """

    return {
        "status": "healthy",
        "service": "recur-ai-revenue-recovery",
    }


@app.get("/analytics/dashboard")
def legacy_analytics_dashboard():
    """
    Legacy analytics endpoint.

    The versioned endpoint is available through
    /api/v1/analytics/dashboard.
    """

    return get_analytics_dashboard()


@app.post("/pipeline/process")
def legacy_process_payment_failure(
    request: FailureRecordRequest,
):
    """
    Legacy payment processing endpoint.

    The versioned endpoint is available through
    /api/v1/pipeline/process.
    """

    record = FailureRecord(
        **request.model_dump()
    )

    result = process_failure(
        record,
        provider=SimulatorProvider(),
    )

    save_pipeline_result(
        result
    )

    return result