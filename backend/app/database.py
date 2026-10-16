from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "forensicvault.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


@event.listens_for(engine, "connect")
def _fk_on(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")          # enforce foreign keys + cascades in SQLite


# Defence in depth: the domain layer rejects children under a Leaf; these triggers make the database refuse it too.
TRIGGERS = [
    """CREATE TRIGGER IF NOT EXISTS trg_leaf_no_children_ins BEFORE INSERT ON evidence
       WHEN NEW.parent_id IS NOT NULL AND (SELECT kind FROM evidence WHERE id = NEW.parent_id) = 'leaf'
       BEGIN SELECT RAISE(ABORT, 'A leaf evidence item cannot have children'); END""",
    """CREATE TRIGGER IF NOT EXISTS trg_leaf_no_children_upd BEFORE UPDATE OF parent_id ON evidence
       WHEN NEW.parent_id IS NOT NULL AND (SELECT kind FROM evidence WHERE id = NEW.parent_id) = 'leaf'
       BEGIN SELECT RAISE(ABORT, 'A leaf evidence item cannot have children'); END""",
]


def init_db():
    from .models import orm  # noqa: F401  (register tables)
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for ddl in TRIGGERS:
            conn.execute(text(ddl))


def get_session():
    return SessionLocal()
