from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./vinyl.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def migrate(engine):
    """Add columns introduced after a database already existed, so an
    existing vinyl.db doesn't need to be recreated to pick up new fields."""
    with engine.connect() as conn:
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(records)").fetchall()}
        if "status" not in cols:
            conn.exec_driver_sql("ALTER TABLE records ADD COLUMN status TEXT NOT NULL DEFAULT 'owned'")
        if "price_currency" not in cols:
            conn.exec_driver_sql("ALTER TABLE records ADD COLUMN price_currency TEXT")
            # Existing prices were entered under whatever the display currency
            # was set to at the time, so that's the best guess for what they're in.
            row = conn.exec_driver_sql(
                "SELECT value FROM settings WHERE key = 'currency'"
            ).fetchone()
            default_currency = row[0] if row and row[0] else "INR"
            conn.exec_driver_sql(
                "UPDATE records SET price_currency = ? WHERE price_currency IS NULL",
                (default_currency,),
            )
        conn.commit()
