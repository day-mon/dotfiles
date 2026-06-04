---
name: fastapi-app-composition
description: Patterns for assembling a FastAPI application — an app-factory function, a lifespan that sets up and tears down resources on app.state, middleware registration order, centralized exception handlers, and the uvicorn entrypoint. Use when creating a FastAPI app, wiring startup/shutdown, adding middleware, or configuring error handling and logging.
---

# FastAPI app composition

Build the app in a factory function, manage resources in a lifespan, register middleware in
reverse execution order, and centralize exception handlers.

## App factory

```python
from importlib import metadata
import fastapi
from myapp.config.app import settings
from myapp.core import error_handlers
from myapp.core.logging import configure_logging
from myapp.core.lifecycle import lifecycle
from myapp.core.middleware.logging import LoggingMiddleware
from myapp.core.middleware.timing import TimingMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
from myapp.api.v1 import router as v1_router

def create_app() -> fastapi.FastAPI:
    configure_logging(json_logs=settings.is_json_logs, log_level=settings.log_level)

    app = fastapi.FastAPI(
        title="My Service",
        version=metadata.version("myapp"),
        lifespan=lifecycle,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # Added in reverse execution order: Timing runs last, CorrelationId first.
    app.add_middleware(TimingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    error_handlers.register(app)
    app.include_router(v1_router)
    return app

app = create_app()
```

- Configure logging **before** creating the app.
- Take the version from package metadata, not a hardcoded string.
- Middleware executes in reverse registration order — add the outermost layer last.

## Lifespan — resources on app.state

Use an `@asynccontextmanager` lifespan to build singletons once, attach them to `app.state`, and
await their teardown on shutdown. Read these singletons from dependencies (see
`fastapi-dependencies`).

```python
import contextlib
import typing
import fastapi
from myapp.core.dependencies import database

@contextlib.asynccontextmanager
async def lifecycle(app: fastapi.FastAPI) -> typing.AsyncGenerator[None, None]:
    app.state.db = database.create()
    client = SomeClient()
    app.state.service = MyService(client=client)

    yield

    await app.state.db.dispose()
    await client.close()
```

Initialize dependencies before the things that consume them; await every close on shutdown.

## Exception handlers

Centralize handlers in a `register(app)` function. Build every error body through one helper so
the response shape is consistent, and log with structured context.

```python
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger()

def _error_response(
    request: Request, exc: Exception, status_code: int, message: str, detail: str, **context
) -> JSONResponse:
    payload: dict[str, object] = {"message": message, "detail": detail, **context}
    logger.error(
        "api_error",
        status_code=status_code, detail=detail, url=str(request.url),
        method=request.method, exc_type=exc.__class__.__name__, exc_message=str(exc),
    )
    return JSONResponse(status_code=status_code, content=payload)

def register(app: fastapi.FastAPI) -> None:
    app.add_exception_handler(SomeUpstreamError, handle_upstream_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_general_exception)
```

Map upstream client failures (e.g. `aiohttp.ClientResponseError` from `fastapi-http-clients`) to
a `424` with a `dependency` context block.

## Entrypoint

Keep `main()` thin; pass the import string so `--reload` works. All config comes from settings.

```python
import uvicorn
from myapp.config.app import settings

def main() -> None:
    uvicorn.run("myapp.app:app", host=settings.host, port=settings.port, reload=settings.reload)

if __name__ == "__main__":
    main()
```

## Logging and middleware

structlog setup and the logging/timing middleware are detailed separately to keep this file
lean: see [references/logging.md](references/logging.md).

## Rules

- Build the app in `create_app()`; expose a module-level `app` as the ASGI target.
- `configure_logging()` runs before `fastapi.FastAPI(...)`.
- Version from `importlib.metadata.version(...)`, never hardcoded.
- Singletons live on `app.state`, created in the lifespan and closed on shutdown.
- Add middleware in reverse execution order.
- Register exception handlers via one `register(app)`; route every error through a shared
  response builder.
- `main()` passes the `"module:app"` import string to `uvicorn.run`; config from settings only.
