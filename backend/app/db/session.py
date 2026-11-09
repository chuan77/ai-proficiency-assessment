"""Database engine, session dependency, and initialisation."""

from collections.abc import Iterator

from sqlalchemy import Engine, inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def build_engine(url: str) -> Engine:
    """Create an engine; SQLite needs check_same_thread disabled for FastAPI."""
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = build_engine(settings.database_url)


def init_db(target: Engine | None = None) -> None:
    """Create all tables if they do not exist."""
    import app.models  # noqa: F401  (registers tables)

    db_engine = target or engine
    SQLModel.metadata.create_all(db_engine)
    _add_missing_columns(db_engine)


def _add_missing_columns(db_engine: Engine) -> None:
    """Lightweight migration: add columns introduced after a database was created."""
    inspector = inspect(db_engine)
    with db_engine.begin() as connection:
        for table in SQLModel.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name not in existing:
                    column_type = column.type.compile(dialect=db_engine.dialect)
                    connection.execute(
                        text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}')
                    )


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a database session."""
    with Session(engine) as session:
        yield session
