"""
database.py - Database Connection and Session Management
=========================================================

This module handles all database-related configuration:
- Creating the SQLite database engine
- Providing session objects for dependency injection

SQLModel uses SQLAlchemy under the hood, so the engine and session
concepts come directly from SQLAlchemy. The engine manages the
connection pool, while sessions represent individual database
conversations (transactions).
"""

from sqlmodel import SQLModel, Session, create_engine

# ---------------------------------------------------------------------------
# Database Engine Configuration
# ---------------------------------------------------------------------------
# We use SQLite for simplicity. The file "bytebooks.db" will be created
# automatically in the project root the first time the app starts.
#
# echo=True prints every SQL statement to the console, which is extremely
# helpful while learning how ORMs translate Python code into SQL queries.
# In production you would set echo=False to reduce log noise.
# ---------------------------------------------------------------------------
DATABASE_URL = "sqlite:///bytebooks.db"

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    """Create all database tables defined by SQLModel models.

    SQLModel.metadata.create_all() inspects every class that inherits from
    SQLModel (with table=True) and issues CREATE TABLE IF NOT EXISTS
    statements so the schema is always up to date.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a database session for FastAPI dependency injection.

    Dependency injection is a design pattern where FastAPI automatically
    calls this function and passes the resulting Session object into any
    endpoint that declares `session: Session = Depends(get_session)`.

    Using a generator (yield) ensures the session is properly closed
    after the request is finished, even if an error occurs.
    """
    with Session(engine) as session:
        yield session
