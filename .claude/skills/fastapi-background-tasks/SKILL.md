---
name: fastapi-background-tasks
description: Patterns for background and scheduled work alongside a FastAPI service — first deciding whether a queue is needed at all, then procrastinate (Postgres-backed) for durable jobs, atomic deferral in the same transaction as the data, periodic tasks, bounded retries, and worker wiring with Dishka. Use when adding asynchronous jobs, periodic tasks (polling, cache warming, cleanup), or offloading slow work out of the request path.
---

# FastAPI background tasks (procrastinate)

Default to **no queue**. Add procrastinate only when the work must survive a restart, needs
retries, or runs on a schedule.

## Do you need a queue?

| Situation | Use |
|---|---|
| Fast enough to finish in the request | Do it inline |
| Cheap follow-up, losing it on restart is fine | FastAPI `BackgroundTasks` |
| Must be durable, retried, scheduled, or run on another process | procrastinate |

Procrastinate over Celery: Postgres is the broker, so there's no Redis or RabbitMQ to run, and
a job commits in the same transaction as the row it processes. Celery has no first-class
Postgres broker.

## App and connector

One procrastinate `App`. It lives in its own Postgres schema, never `public`.

```python
import procrastinate
from myapp.core.config.database import db_settings

queue = procrastinate.App(
    connector=procrastinate.PsycopgConnector(
        conninfo=db_settings.db.conninfo,
        kwargs={"options": "-c search_path=procrastinate"},
    ),
    import_paths=["myapp.jobs"],
)
```

Apply procrastinate's own schema in the deploy step with `procrastinate --app=myapp.queue.queue
schema --apply`. Alembic owns app tables only; the drift check excludes the `procrastinate`
schema (see `fastapi-alembic`).

## Defer atomically with the state change

Pass the session's driver connection to `configure(connection=...)`. The job INSERT runs inside
your transaction, so the row and the job commit together or not at all. No outbox needed.

```python
class TicketIntake:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    async def accept(self, *, event_key: str) -> None:
        async with self.sessions.begin() as session:
            session.add(Run(event_key=event_key, outcome="pending"))
            await session.flush()
            connection = await self._driver_connection(session)
            await analyze_ticket.configure(connection=connection).defer_async(event_key=event_key)

    @staticmethod
    async def _driver_connection(session: AsyncSession) -> psycopg.AsyncConnection:
        raw = await (await session.connection()).get_raw_connection()
        return raw.driver_connection
```

- Requires the `postgresql+psycopg` driver (psycopg 3). asyncpg connections are rejected.
- The app engine's `search_path` must include `procrastinate`
  (`connect_args={"options": "-c search_path=public,procrastinate"}`) so the defer finds its
  functions.
- A queueing-lock violation aborts the whole transaction. Wrap the defer in
  `session.begin_nested()` when the change should commit anyway.
- Never `defer_async()` on the app's own pool before or after the commit; that is the race this
  pattern removes.

## Tasks are thin and carry IDs

Tasks take identifiers, reread current state, and delegate to one service. The worker has no
FastAPI `Depends`, so it resolves services from a Dishka container (see `codebase-design`).

```python
@queue.task(
    queue="tickets",
    retry=procrastinate.RetryStrategy(
        max_attempts=3,
        exponential_wait=5,
        retry_exceptions={UpstreamUnavailableError},
    ),
)
async def analyze_ticket(event_key: str) -> None:
    async with container() as scope:
        analyzer = await scope.get(TicketAnalyzer)
        await analyzer.run(event_key=event_key)
```

- Tasks are idempotent; a retry or a stalled-job rescue can run them twice.
- When arguments are more than IDs, validate them with a pydantic model on the first line.
- Tasks never touch FastAPI request or `app.state`.

## Bounded retries, then fail visibly

`RetryStrategy` sets `max_attempts` and `retry_exceptions`. Without them procrastinate retries
forever or on every exception, so always set both. Retry only errors a retry can fix.

After the last attempt the job is `failed`. Procrastinate's job table is not the business
record: on the final attempt (`pass_context=True`, then check
`task.retry.get_retry_decision(...) is None`) the task writes `outcome="failed"` on its run row
and re-raises. Alerting reads that row. A person retries with
`queue.job_manager.retry_job_by_id_async(...)`. Nothing auto-requeues a failed job.

## Periodic tasks

Workers defer periodic tasks; the database ensures one defer per period across all workers.
Periodic tasks receive the scheduled `timestamp`; use it instead of `time.time()`.

```python
@queue.periodic(cron="0 3 * * *")
@queue.task(queueing_lock="refresh_history")
async def refresh_history(timestamp: int) -> None:
    async with container() as scope:
        await (await scope.get(HistoryRefresher)).run(as_of=timestamp)
```

## Stalled jobs

A worker killed mid-job leaves it `doing` forever. Rescue those once, then surface the rest.

```python
STALL_RESCUE_LIMIT: Final = 2
log = structlog.get_logger()


@queue.periodic(cron="*/10 * * * *")
@queue.task(queueing_lock="retry_stalled_jobs")
async def retry_stalled_jobs(timestamp: int) -> None:
    for job in await queue.job_manager.get_stalled_jobs():
        if job.attempts >= STALL_RESCUE_LIMIT:
            log.error("job_stalled", job_id=job.id, task=job.task_name, attempts=job.attempts)
            continue
        await queue.job_manager.retry_job(job)
```

## Running the worker

Default: its own process, scaled independently of the API.

```python
async def main() -> None:
    async with queue.open_async():
        try:
            await queue.run_worker_async()
        finally:
            await container.close()
```

Running the worker inside the API lifespan is allowed for small services; follow the
one-uvicorn-worker and shutdown-budget rules in `fastapi-app-composition`, and pass
`install_signal_handlers=False`.

## Escape hatch: FastAPI BackgroundTasks

For cheap, in-process follow-ups that don't need durability or retries:

```python
@router.post("/items")
async def create_item(item: ItemIn, background: fastapi.BackgroundTasks) -> ItemOut:
    saved = await save(item)
    background.add_task(send_notification, saved.id)
    return saved
```

## Rules

- No queue until the work must be durable, retried, or scheduled; then procrastinate.
- One procrastinate `App` in its own schema; connection info comes from settings.
- Defer with `configure(connection=...)` inside the transaction that writes the row.
- Tasks carry IDs, stay idempotent, and resolve services from a Dishka container.
- Every task with retries sets `max_attempts` and `retry_exceptions`.
- Failure is recorded on a run row and retried by a person, never auto-requeued.
- Rescue stalled jobs a bounded number of times; log the rest as `job_stalled`.
- Periodic tasks use `@queue.periodic` with a `queueing_lock`.
- `BackgroundTasks` only for trivial, non-durable in-process follow-ups.
