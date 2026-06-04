---
name: fastapi-alembic
description: Async Alembic setup for SQLAlchemy in a FastAPI service — an env.py that runs migrations through an async engine via asyncio.run and connection.run_sync, plus idempotent, dialect-aware migration files (existence checks; sqlite table-recreate vs postgres ALTER). Use when configuring Alembic, writing migrations, or supporting both SQLite and PostgreSQL.
---

# FastAPI + async Alembic

Run migrations through the async engine and write migrations that are idempotent and portable
across SQLite and PostgreSQL.

## Async env.py

Point `target_metadata` at the same `Base.metadata` your models use, build an async engine from
the app's `connection_url`, and bridge to Alembic's sync API with `connection.run_sync`.

```python
from __future__ import annotations
import asyncio
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from myapp.config.database import settings as db_settings
from myapp.models import Base

target_metadata = Base.metadata

def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    engine = create_async_engine(db_settings.db.connection_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

run_migrations_online()
```

The `connection_url` is the same discriminated-union setting from `fastapi-config`, and the
metadata is the `DeclarativeBase` from `fastapi-sqlalchemy`.

## Migration file header

Standard Alembic revision identifiers; keep `upgrade`/`downgrade` symmetric.

```python
"""Create game_results table.

Revision ID: 001
Revises:
Create Date: 2026-05-01 00:00:00
"""
from __future__ import annotations
import typing
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: str | None = None
branch_labels: str | typing.Sequence[str] | None = None
depends_on: str | typing.Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "game_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("game_id", sa.String(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table("game_results")
```

## Idempotent, dialect-aware migrations

When a migration may run against an already-partially-migrated DB, guard changes with existence
checks. When SQLite and PostgreSQL need different mechanics (SQLite can't `ALTER` to add
constraints/FKs and needs a table rebuild), branch on the dialect.

```python
from sqlalchemy import inspect

def _column_exists(table: str, column: str) -> bool:
    inspector = inspect(op.get_bind())
    return column in {c["name"] for c in inspector.get_columns(table)}

def upgrade() -> None:
    dialect = op.get_context().dialect.name
    if dialect == "sqlite":
        _upgrade_sqlite()   # batch_alter_table / table recreate
    else:
        _upgrade_postgres()  # op.add_column + op.create_foreign_key
```

Use `op.batch_alter_table(...)` for the SQLite rebuild path.

## Rules

- `target_metadata = Base.metadata` from your models; never maintain a second metadata.
- Online migrations run via `create_async_engine` + `connection.run_sync(do_run_migrations)`
  inside `asyncio.run(...)`.
- Read the DB URL from settings (`fastapi-config`), not from `alembic.ini` hardcoding.
- Always implement `downgrade`.
- Guard schema changes with existence checks; branch on `op.get_context().dialect.name` when
  SQLite and PostgreSQL diverge.
