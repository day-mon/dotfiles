# ORM patterns

Reference for `fastapi-sqlalchemy`. SQLAlchemy 2.x.

## Contents
- Hybrid properties (and `correlate_except`)
- Composites for value objects
- Ordered children and association proxies
- Tables the app doesn't own
- Postgres specifics
- Type-checker gotchas

## Hybrid properties

A derived field works on a loaded object and inside a query. Use the `inplace` form.

```python
from sqlalchemy import ColumnElement, case, select
from sqlalchemy.ext.hybrid import hybrid_property

class Run(Base):
    @hybrid_property
    def status(self) -> str:
        if self.outcome is not None:
            return "completed"
        return JOB_STATUS.get(self.job.status, "unavailable") if self.job else "unavailable"

    @status.inplace.expression
    @classmethod
    def _status_expression(cls) -> ColumnElement[str]:
        job_status = (
            select(Job.status)
            .where(Job.id == cls.job_id)
            .correlate_except(Job)
            .scalar_subquery()
        )
        return case(
            (cls.outcome.is_not(None), "completed"),
            *((job_status == key, value) for key, value in JOB_STATUS.items()),
            else_="unavailable",
        )
```

- **Every scalar subquery in a hybrid needs `.correlate_except(Inner)`.** Without it, a query
  that doesn't otherwise select `cls` (a `GROUP BY` facet, a count) puts `cls` in the
  subquery's own `FROM`, and Postgres fails with "more than one row returned by a subquery".
- Test each hybrid by selecting it in SQL and reading it off a loaded row for the same record;
  the values must match.

## Composites for value objects

Several columns that only make sense together become one attribute.

```python
from dataclasses import dataclass
from sqlalchemy.orm import Mapped, composite, mapped_column

@dataclass(frozen=True, slots=True)
class PageTarget:
    kind: str
    page_id: str | None

class Finding(Base):
    target: Mapped[PageTarget] = composite(
        mapped_column("target_kind", String(16)),
        mapped_column("target_page_id", String(32)),
    )

select(Finding).where(Finding.target == PageTarget("existing_page", "131"))
```

Give the dataclass `of(contract)` / `to_contract()` methods when it mirrors an API model.

## Ordered children and association proxies

```python
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.orderinglist import ordering_list

class Finding(Base):
    topics: Mapped[list[FindingTopic]] = relationship(
        order_by=FindingTopic.position,
        collection_class=ordering_list("position"),
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    topic_keys: AssociationProxy[list[str]] = association_proxy(
        "topics", "key", creator=lambda key: FindingTopic(key=key)
    )
```

`ordering_list` fills `position` on assignment; replace the whole list
(`finding.topics = [...]`) rather than mutating it item by item.

## Tables the app doesn't own

Map only the columns you read, read-only, and keep them out of migrations.

```python
EXTERNAL = {"schema": "public", "info": {"external": True}}

class QueueJob(Base):
    __tablename__ = "jobs"
    __table_args__ = EXTERNAL
    status: Mapped[str] = mapped_column(ENUM(..., name="job_status", schema="public", create_type=False))
```

- `ENUM(..., create_type=False, schema=...)` reuses the existing database type.
- Relationships to them use `viewonly=True`.
- Alembic skips them with `include_object` (see `fastapi-alembic`).
- Declaring them lets the app's foreign keys resolve and lets queries join on them.

## Postgres specifics

- Latest row per key: `select(M).ext(postgresql.distinct_on(M.key)).order_by(M.key, M.at.desc())`
  (`.distinct(col)` is deprecated). Wrap it with `aliased(M, subquery)` to filter the result.
- Claims: `.with_for_update(skip_locked=True)` so concurrent workers take disjoint rows.
- Upserts: `postgresql.insert(M).on_conflict_do_nothing()` /
  `.on_conflict_do_update(index_elements=[...], set_={...})`.
- Filtered aggregates: `func.count(distinct(M.col)).filter(M.role == "support")`.
- Prefix search: `col.istartswith(value, autoescape=True)` so `%` and `_` are literal.

## Type-checker gotchas

- Columns inherited from a mixin aren't visible as `update(M).values(col=...)` keywords to
  pyright/pyrefly. Use `values({M.col: value})`.
- Annotate select builders with the row type (`Select[str, int]`) instead of `Select[Any]`.
