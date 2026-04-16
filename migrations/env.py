"""
Alembic environment.

Reads the database URL from the application settings (so we don't duplicate
config). Imports api.models so autogenerate sees every table.

Async support: Alembic itself is sync, so we run migrations through a sync
engine derived from DATABASE_URL by swapping the driver to psycopg.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from api.config import settings
from api.database import Base
import api.models  # noqa: F401  — register models with Base.metadata


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Swap async driver for the sync one Alembic needs.
sync_url = settings.database_url.replace("+asyncpg", "+psycopg")
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
