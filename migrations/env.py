"""Migrations run only with a caller-owned SQLAlchemy connection and guard."""
from alembic import context
from geoai.storage.db_models import Base

config = context.config
target_metadata = Base.metadata
connection = config.attributes.get("connection")
lease = config.attributes.get("guard_lease")
project_id = config.attributes.get("project_id")
if connection is None or lease is None or project_id is None:
    raise RuntimeError("migration requires guarded application connection and lease")
lease.assert_held(project_id)

context.configure(connection=connection, target_metadata=target_metadata,
                  render_as_batch=True, transactional_ddl=True)
with context.begin_transaction():
    context.run_migrations()

