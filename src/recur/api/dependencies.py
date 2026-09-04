"""FastAPI dependency providers for the application composition root."""
from __future__ import annotations

from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from recur.config import Settings, get_settings
from recur.execution import PaymentProvider, SimulatorProvider
from recur.persistence.database import SessionLocal
from recur.services.recovery_service import RecoveryService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache
def get_payment_provider() -> PaymentProvider:
    settings: Settings = get_settings()
    if settings.payment_provider.lower() != "simulator":
        raise NotImplementedError(
            "Only the simulator payment provider is currently configured."
        )
    return SimulatorProvider()


def get_recovery_service(
    db: Session = Depends(get_db),
    provider: PaymentProvider = Depends(get_payment_provider),
) -> RecoveryService:
    return RecoveryService(db=db, provider=provider)