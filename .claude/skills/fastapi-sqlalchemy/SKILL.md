---
name: fastapi-sqlalchemy
description: Async SQLAlchemy 2.0 patterns for FastAPI services — a DeclarativeBase, Mapped/mapped_column typing, reusable PK/timestamp/CRUD mixins, relationships with lazy="selectin", an async engine/session-factory wired through app.state, and the get_session yield dependency. Use when defining models, mixins, relationships, or querying the database in an async FastAPI service.
---

# FastAPI + async SQLAlchemy

Models are typed with `Mapped`/`mapped_column`, compose reusable mixins, and are queried through
an async session injected as a dependency.

## Declarative base and models

```python
import datetime
import typing
import sqlalchemy
import sqlalchemy.orm
from myapp.models import mixins

class Base(sqlalchemy.orm.DeclarativeBase):
    """Base class for declarative models."""

class GameResult(Base, mixins.IDMixin, mixins.TimestampMixin, mixins.CRUDMixin):
    __tablename__ = "game_results"
    __table_args__ = (
        sqlalchemy.UniqueConstraint("game_id", "model_id", name="uq_game_model"),
    )

    game_id: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(index=True)
    date: sqlalchemy.orm.Mapped[datetime.date] = sqlalchemy.orm.mapped_column(index=True)
    home_score: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column()
    confidence: sqlalchemy.orm.Mapped[float | None] = sqlalchemy.orm.mapped_column(nullable=True)
    kind: sqlalchemy.orm.Mapped[typing.Literal["win-loss", "over-under"]] = (
        sqlalchemy.orm.mapped_column()
    )
    model_id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        sqlalchemy.ForeignKey("ml_models.id"), index=True
    )
```

- Always type columns as `Mapped[...]`; nullability comes from `T | None` plus `nullable=True`.
- Use `typing.Literal[...]` for closed-set string columns.
- Indexes/constraints go in `__table_args__`.

## Mixins

Compose a model from `Base` plus mixins. Three standard ones:

```python
# pk.py
class IDMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
```

```python
# timestamp.py
class TimestampMixin:
    updated_at: Mapped[datetime.datetime] = mapped_column(
        index=True,
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
```

```python
# crud.py — async classmethods shared by every model
class CRUDMixin:
    @classmethod
    async def create(cls, session, **kwargs) -> Self: ...
    @classmethod
    async def get_or_raise(cls, session, pk) -> Self: ...
    @classmethod
    async def filter_one(cls, session, **kwargs) -> Self | None: ...
    # ... full catalogue in references/crud-mixin.md
```

The `CRUDMixin` gives every model `create`/`get`/`filter`/`update`/`upsert`/`delete`/`count`/
`exists` as async classmethods that take the session. The complete method list with signatures
is in [references/crud-mixin.md](references/crud-mixin.md).

## Relationships

Type relationships with `Mapped[...]` and prefer `lazy="selectin"` for async loading (lazy
attribute access can't issue I/O under async).

```python
class GameResult(Base, ...):
    model: Mapped["MLModel"] = relationship(back_populates="game_results", lazy="selectin")

class MLModel(Base, ...):
    game_results: Mapped[list["GameResult"]] = relationship(
        back_populates="model", cascade="all, delete-orphan", lazy="selectin",
    )
```

For a value that is both a Python property and a SQL expression, use `@hybrid_property` with
`.inplace.expression`:

```python
@hybrid_property
def total_score(self) -> int:
    return self.home_score + self.away_score

@total_score.inplace.expression
@classmethod
def _total_score_expr(cls) -> sqlalchemy.ColumnElement[int]:
    return cls.home_score + cls.away_score
```

## Engine, session factory, and the session dependency

Wrap the engine and `async_sessionmaker` in a small dataclass, create it in the lifespan, and
store it on `app.state`. The `get_session` dependency opens one session per request.

```python
import dataclasses
import typing
import fastapi
import sqlalchemy.ext.asyncio as sa_async
from myapp.config.database import settings

@dataclasses.dataclass(slots=True)
class Database:
    engine: sa_async.AsyncEngine
    session_factory: sa_async.async_sessionmaker[sa_async.AsyncSession]

    async def dispose(self) -> None:
        await self.engine.dispose()

def create() -> Database:
    engine = sa_async.create_async_engine(settings.db.connection_url, echo=settings.echo)
    factory = sa_async.async_sessionmaker(engine, expire_on_commit=settings.expire_on_commit)
    return Database(engine=engine, session_factory=factory)

async def get_session(
    request: fastapi.Request,
) -> typing.AsyncGenerator[sa_async.AsyncSession, None]:
    async with request.app.state.db.session_factory() as session:
        yield session

Session = typing.Annotated[sa_async.AsyncSession, fastapi.Depends(get_session)]
```

`create()` is called in the lifespan (`app.state.db = database.create()`) — see
`fastapi-app-composition`. `Session` is injected into services per `fastapi-module-structure`.
The `connection_url` comes from the discriminated-union DB settings in `fastapi-config`.

## Rules

- Type every column as `Mapped[...]` with `mapped_column(...)`; `Literal` for enums.
- Compose models from `Base` + mixins; don't redefine `id`/timestamps per model.
- Use async sessions only; relationships use `lazy="selectin"`.
- One engine + one `async_sessionmaker` for the app, stored on `app.state.db`.
- One session per request via the `get_session` yield dependency; never share sessions.
- Migrations are managed with Alembic — see `fastapi-alembic`.
