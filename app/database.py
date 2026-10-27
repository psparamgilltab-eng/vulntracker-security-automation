
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Secure scan search
# ---------------------------------------------------------------------------

def search_scans_by_query(db, query: str, owner_id: int) -> list:
    """
    Search scans belonging only to the specified user.

    Bound parameters prevent user input from being interpreted as SQL code.
    The owner_id condition prevents cross-user search results.
    """
    sql = text(
        """
        SELECT
            id,
            title,
            description,
            severity,
            status,
            cve_id,
            affected_component,
            owner_id,
            created_at
        FROM scan_results
        WHERE owner_id = :owner_id
          AND (
              title LIKE :pattern
              OR description LIKE :pattern
              OR cve_id LIKE :pattern
          )
        ORDER BY created_at DESC
        """
    )

    result = db.execute(
        sql,
        {
            "owner_id": owner_id,
            "pattern": f"%{query}%",
        },
    )

    return [dict(row._mapping) for row in result]
