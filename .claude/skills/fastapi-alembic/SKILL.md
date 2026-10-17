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

## Migrations never import app code

Freeze any value a migration depends on (allowed values for a check constraint, a default) as a
module constant, and add an app test that compares the frozen copy with its source.

```python
# versions/011_findings.py
COVERAGE = ("covered", "absent", "outdated")

# tests/test_migrations.py
def test_coverage_constraint_matches_contract():
    assert load_migration("011_findings").COVERAGE == get_args(DocumentationCoverage)
```

## Detect model/migration drift

Run every migration against the real engine (testcontainers), then diff against the models.
App tables must show no differences.

```python
command.upgrade(Config("alembic.ini"), "head")
with engine.connect() as conn:
    ctx = MigrationContext.configure(conn, opts={"include_schemas": True, "include_object": include_object})
    assert compare_metadata(ctx, Base.metadata) == []
```

Skip tables the app maps but doesn't own, and procrastinate's schema (it migrates itself):

```python
def include_object(item, name, type_, reflected, compare_to) -> bool:
    if type_ != "table":
        return True
    return item.schema != "procrastinate" and not item.info.get("external")
```

## Backfill or reset

When a schema change makes old rows unreadable, choose deliberately: backfill when the data
matters, clear and regenerate when it's disposable. State the choice and the reason in the
migration docstring, and say which environments it affects.

## Rules

- `target_metadata = Base.metadata` from your models; never maintain a second metadata.
- Online migrations run via `create_async_engine` + `connection.run_sync(do_run_migrations)`
  inside `asyncio.run(...)`.
- Read the DB URL from settings (`fastapi-config`), not from `alembic.ini` hardcoding.
- Always implement `downgrade`.
- Never import app code from a migration; freeze what it needs and test the copy.
- Check for model/migration drift against the real engine in CI.
- Guard schema changes with existence checks; branch on `op.get_context().dialect.name` when
  SQLite and PostgreSQL diverge.
