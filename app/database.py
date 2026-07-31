import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Reads DATABASE_URL from the environment so we can point at SQLite locally
# and swap it later without touching code (e.g. for a managed Postgres).
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shortener.db")

# SQLite needs this flag when used with FastAPI's threaded request handling.
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
