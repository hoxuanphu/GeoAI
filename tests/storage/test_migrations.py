import importlib.util
import tempfile
import unittest
from pathlib import Path

DB_AVAILABLE = all(importlib.util.find_spec(name) for name in ("sqlalchemy", "alembic"))
if DB_AVAILABLE:
    from sqlalchemy import create_engine, inspect, text
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from geoai.storage.db_models import Base
    from geoai.storage.repository import migrate_project
    from test_repository import FixtureGuard


@unittest.skipUnless(DB_AVAILABLE, "SQLAlchemy and Alembic DB extra unavailable")
class MigrationTests(unittest.TestCase):
    def test_initial_schema_and_foreign_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "project.sqlite"
            guard = FixtureGuard("project:one")
            migrate_project(db, "project:one", guard)
            engine = create_engine(f"sqlite:///{db.as_posix()}")
            names = set(inspect(engine).get_table_names())
            self.assertTrue({"jobs", "attempts", "publications", "artifacts", "dependency_pins", "dependency_leases", "alembic_version"} <= names)
            self.assertTrue(inspect(engine).get_foreign_keys("attempts"))
            self.assertTrue(inspect(engine).get_indexes("jobs"))
            with engine.connect() as conn:
                self.assertEqual(conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one(), "0001_initial")
                changes = compare_metadata(MigrationContext.configure(conn), Base.metadata)
                self.assertEqual(changes, [])
            engine.dispose()
            guard.close()
