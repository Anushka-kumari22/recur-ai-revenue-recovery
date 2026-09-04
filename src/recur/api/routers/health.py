from fastapi import APIRouter
from sqlalchemy import text

from recur.persistence.database import engine


router = APIRouter(
    tags=["Health"],
)


@router.get("/health")
def health_check() -> dict:
    """
    Basic liveness check.

    Confirms that the API process is running.
    """

    return {
        "status": "healthy",
        "service": "recur-ai-revenue-recovery",
    }


@router.get("/ready")
def readiness_check() -> dict:
    """
    Readiness check.

    Confirms that the API and database are ready
    to serve requests.
    """

    with engine.connect() as connection:
        connection.execute(
            text("SELECT 1")
        )

    return {
        "status": "ready",
        "database": "connected",
    }