'''
engine.py has one responsibility:
    Define the shared database connection infrastructure for your app:
    - how to connect (DATABASE_URL)
    - the SQLAlchemy engine (pool + connections)
    - the Session factory (sessionmaker)

This file must live in Infrastructure because:
    - it's pure “talk to the outside world” code (PostgreSQL)
    - Domain/Business must not depend on it
'''

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _build_database_url() -> str:
    """
    Build the DB URL from environment variables.

    Why env vars?
    - Works locally and in cloud (Render) the same way
    - Keeps secrets out of code
    - Matches Docker/CI best practices
    """
    user = os.getenv("POSTGRES_USER", "alberto")
    password = os.getenv("POSTGRES_PASSWORD", "123456")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    db = os.getenv("POSTGRES_DB", "project2db")

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"


DATABASE_URL: str = _build_database_url()

# Long-lived engine (connection pool manager)
engine = create_engine(
    DATABASE_URL,
    echo=False,        # set True only while debugging SQL output
    pool_pre_ping=True # avoids stale connections in long-running apps
)

# Session factory (create short-lived sessions)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db_session():
    """
    Dependency-style generator:
    - creates a session
    - yields it
    - ensures it's always closed

    Later, FastAPI will use this with Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

