---
name: fastapi-background-tasks
description: Patterns for background and scheduled work alongside a FastAPI service, preferring Celery — task definitions, a broker and result backend, dispatching from request handlers, and periodic schedules via Celery beat. Use when adding asynchronous jobs, periodic tasks (polling, cache warming, cleanup), or offloading slow work out of the request path.
---

# FastAPI background tasks (Celery)

Default to **Celery** for background and recurring work. Run it as a separate worker process so
slow or scheduled jobs never block the API event loop. Use FastAPI's built-in `BackgroundTasks`
only for trivial in-process follow-ups (see the escape hatch below).

## Celery app

Define one Celery app. Read the broker and result backend from settings so they follow the same
discriminated-union/env conventions as everything else (see `fastapi-config`).

```python
import celery
from myapp.config.celery import settings

app = celery.Celery(
    "myapp",
    broker=settings.broker_url,
    backend=settings.result_backend_url,
    include=["myapp.tasks"],
)
```

## Task definitions

Keep tasks small, typed, and **idempotent** — they can be retried. Tasks do their own work; they
don't import FastAPI request state.

```python
from myapp.celery_app import app

@app.task(bind=True, max_retries=3)
def refresh_history(self, model_name: str) -> None:
    ...
```

## Dispatching from a request handler

Enqueue with `.delay(...)` (or `.apply_async(...)` when you need options like `eta`/`countdown`),
then return immediately. Do not `.get()` the result inside the request — that blocks.

```python
from myapp.tasks import refresh_history

@router.post("/history/refresh", status_code=202)
async def trigger_refresh(model_name: str) -> dict[str, str]:
    task = refresh_history.delay(model_name)
    return {"task_id": task.id}
```

## Periodic tasks (Celery beat)

Schedule recurring work with beat. Name interval constants — no magic numbers.

```python
from datetime import timedelta

app.conf.beat_schedule = {
    "refresh-history-daily": {
        "task": "myapp.tasks.refresh_history",
        "schedule": timedelta(days=1),
        "args": ("default",),
    },
}
```

Run the worker and beat as their own processes, e.g. `celery -A myapp.celery_app worker` and
`celery -A myapp.celery_app beat`.

## Escape hatch: FastAPI BackgroundTasks

For cheap, in-process follow-ups that don't need durability or retries (e.g. firing off a log or
a notification after responding), use the built-in tool instead of Celery:

```python
@router.post("/items")
async def create_item(item: ItemIn, background: fastapi.BackgroundTasks) -> ItemOut:
    saved = await save(item)
    background.add_task(send_notification, saved.id)
    return saved
```

## Rules

- Prefer Celery for anything that is slow, must survive a restart, needs retries, or runs on a
  schedule.
- One Celery app; broker and result backend come from settings, not hardcoded.
- Tasks are idempotent and don't depend on request/app state.
- Dispatch with `.delay()`/`.apply_async()` and return promptly; never block on `.get()` in a
  request.
- Schedule recurring work with Celery beat using named interval constants.
- Use FastAPI `BackgroundTasks` only for trivial, non-durable in-process follow-ups.
