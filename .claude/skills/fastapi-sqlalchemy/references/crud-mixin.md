# CRUDMixin method catalogue

Reference for `fastapi-sqlalchemy`. A mixin of async classmethods shared by every model. Each
takes an `AsyncSession` as the first argument and commits where it mutates. All are `@classmethod`
and `async`.

## Contents
- Type aliases
- Create / get-or-create
- Read (get, get_or_raise, filter_one, list, filter, search)
- Update (update, update_or_raise, upsert)
- Delete (delete, delete_or_raise, bulk_delete)
- Aggregates (count, exists)
- Usage

## Type aliases

```python
type FilterDict = dict[str, object]
type OrderByClause = list[ColumnElement[object] | InstrumentedAttribute[object]]
```

## Create / get-or-create

```python
async def create(cls, session, **kwargs) -> Self
# add + commit + refresh, returns the persisted instance

async def get_or_create(cls, session, defaults: FilterDict | None = None, **kwargs) -> tuple[Self, bool]
# returns (instance, created); create_kwargs = {**defaults, **kwargs}
```

## Read

```python
async def get(cls, session, pk) -> Self | None
# session.get(cls, pk)

async def get_or_raise(cls, session, pk) -> Self
# get, else raise NoResultFound

async def filter_one(cls, session, **kwargs) -> Self | None
# select(cls).filter_by(**kwargs).limit(1) -> first

async def list(cls, session, limit=None, offset=None, order_by: OrderByClause | None = None) -> Sequence[Self]

async def filter(cls, session, *, filters: FilterDict | None = None,
                 or_filters: FilterDict | None = None,
                 limit=None, offset=None, order_by=None) -> Sequence[Self]
# AND across `filters`, OR across `or_filters`; combined => and_(*and, or_(*or))

async def search(cls, session, column: str, query: str, *,
                 case_sensitive: bool = False, limit=None, offset=None) -> Sequence[Self]
# col.like / col.ilike with %query%
```

## Update

```python
async def update(cls, session, pk, **kwargs) -> Self | None
# get by pk, setattr each field, commit + refresh; None if missing

async def update_or_raise(cls, session, pk, **kwargs) -> Self
# update, else raise NoResultFound

async def upsert(cls, session, **kwargs) -> Self
# session.merge(cls(**kwargs)) + commit + refresh
```

## Delete

```python
async def delete(cls, session, pk) -> bool
# delete by pk; True if a row was removed

async def delete_or_raise(cls, session, pk) -> None
# delete, else raise NoResultFound

async def bulk_delete(cls, session, **filters) -> int
# delete all rows matching filters; returns count
```

## Aggregates

```python
async def count(cls, session, **filters) -> int
# select(func.count()).select_from(cls) [+ where AND-clauses]

async def exists(cls, session, **kwargs) -> bool
# count(...) > 0
```

## Usage

From inside a service (which holds the session — see `fastapi-module-structure`):

```python
class HistoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_model(self, name: str) -> MLModel:
        if not (model := await MLModel.filter_one(self.session, name=name)):
            raise NoResultFound(f"MLModel {name!r} not found")
        return model
```
