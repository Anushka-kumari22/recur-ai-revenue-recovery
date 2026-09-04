from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)

from recur.config import get_settings


settings = get_settings()

DATABASE_URL = settings.database_url

database_url = make_url(DATABASE_URL)

connect_args: dict = {}

if database_url.get_backend_name() == "sqlite":
    connect_args["check_same_thread"] = False


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy database models.
    """

    pass


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def create_database_tables() -> None:
    """
    Create all registered database tables.
    """

    from recur.persistence import models

    Base.metadata.create_all(
        bind=engine,
    )