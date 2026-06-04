---
name: fastapi-dependencies
description: Patterns for FastAPI dependency injection — reusable Annotated[..., Depends(...)] type aliases, yield dependencies with request/function scope for cleanup, preferring a function that returns an instance over class dependencies, and shared parameter objects like pagination. Use when adding or refactoring FastAPI dependencies, shared parameters, or injectables.
---

# FastAPI dependencies

Inject via reusable `Annotated` type aliases, not inline `Depends()` calls scattered through
signatures.

## When to use a dependency

Reach for a dependency when the logic:

- can't be expressed as plain Pydantic validation and needs real code,
- touches external resources or may block,
- is a sub-dependency another dependency needs,
- is shared across endpoints (auth, early errors, common params),
- needs cleanup (DB sessions, file handles) — use `yield`,
- needs request data (headers, query params, etc.).

## Type-alias pattern

Define the dependency function, then export an `Annotated` alias. Inject the alias.

```python
import typing
import fastapi
import sqlalchemy.ext.asyncio

async def get_session(
    request: fastapi.Request,
) -> typing.AsyncGenerator[sqlalchemy.ext.asyncio.AsyncSession, None]:
    async with request.app.state.db.session_factory() as session:
        yield session

Session = typing.Annotated[
    sqlalchemy.ext.asyncio.AsyncSession,
    fastapi.Depends(get_session),
]
```

```python
@router.post("")
async def create_prediction(data: PredictionIn, session: Session) -> PredictionOut: ...
```

The alias (`Session`, `CacheDep`, `PaginationDep`, ...) is the unit other modules import and
reuse — never repeat the `Depends(...)` call.

## yield dependencies and scope

`yield` dependencies run teardown after the `yield`. `scope` controls *when*:

- `scope="request"` (default) — teardown runs **after** the response is sent.
- `scope="function"` — teardown runs after the response data is generated but **before** it is
  sent.

```python
async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        await db.close()

DBDep = typing.Annotated[DBSession, fastapi.Depends(get_db)]  # request scope
```

```python
def get_username():
    try:
        yield "rick"
    finally:
        print("cleanup before response is sent")

UserName = typing.Annotated[str, fastapi.Depends(get_username, scope="function")]
```

## Prefer functions over class dependencies

Avoid class dependencies. If you need an object, write a function that builds and returns it.

```python
import dataclasses

@dataclasses.dataclass(slots=True)
class Paginator:
    offset: int = 0
    limit: int = 100
    q: str | None = None

def get_paginator(offset: int = 0, limit: int = 100, q: str | None = None) -> Paginator:
    return Paginator(offset=offset, limit=limit, q=q)

PaginatorDep = typing.Annotated[Paginator, fastapi.Depends(get_paginator)]
```

Do NOT inject a bare class with `Annotated[Paginator, fastapi.Depends()]`.

## Shared parameter objects (pagination)

A small dataclass keeps list endpoints consistent and computes derived values once.

```python
@dataclasses.dataclass(slots=True)
class Pagination:
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

def get_pagination(
    page: typing.Annotated[int, fastapi.Query(ge=1)] = 1,
    page_size: typing.Annotated[int, fastapi.Query(ge=1, le=100)] = 20,
) -> Pagination:
    return Pagination(page=page, page_size=page_size)

PaginationDep = typing.Annotated[Pagination, fastapi.Depends(get_pagination)]
```

Use 1-based pages; expose `offset` for the query layer.

## Rules

- MUST inject via a named `Annotated[T, fastapi.Depends(fn)]` alias; do not inline `Depends()`.
- Use `yield` for anything needing cleanup; pick `scope` deliberately (`request` default).
- Prefer a function returning an instance over a class dependency.
- Singletons (cache, db handle) live on `app.state` and are read inside the dependency — see
  `fastapi-app-composition`.
- Honor the async/sync rule from `fastapi-routing`: blocking dependency → plain `def`.
