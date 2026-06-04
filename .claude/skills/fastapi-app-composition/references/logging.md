# structlog logging and request middleware

Reference for `fastapi-app-composition`: how to configure structlog and the logging/timing
middleware.

## Contents
- Shared processors and `configure_logging`
- Correlation-id processor
- JSON vs console rendering
- Logging middleware (contextvar binding)
- Timing middleware

## Shared processors and configure_logging

Define the processor chain once and reuse it for both structlog and the stdlib
`ProcessorFormatter`, so logs from libraries are formatted the same as your own.

```python
import logging
import typing
import structlog
from asgi_correlation_id import correlation_id

def _add_correlation_id(
    logger: object, method: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    event_dict["correlation_id"] = correlation_id.get() or "-"
    return event_dict

_SHARED_PROCESSORS: list[structlog.types.Processor] = [
    structlog.contextvars.merge_contextvars,
    _add_correlation_id,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
]

def configure_logging(
    json_logs: bool = False,
    log_level: typing.Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
) -> None:
    structlog.configure(
        processors=[*_SHARED_PROCESSORS, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
        foreign_pre_chain=_SHARED_PROCESSORS,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

- Inject the correlation id (from `asgi-correlation-id`) into every line.
- JSON renderer in production, console renderer in development — driven by settings.
- `merge_contextvars` pulls in any contextvars bound per request (see below).

## Logging middleware (contextvar binding)

Bind request metadata to structlog contextvars at the start of each request so every downstream
log line inherits it. Clear contextvars first to prevent leakage between requests.

```python
import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )
        logger.info("request_received", user_agent=request.headers.get("user-agent", "-"))
        response = await call_next(request)
        logger.info("request_completed", status_code=response.status_code)
        return response
```

## Timing middleware

Measure with a monotonic clock, expose the duration as a header, and log at debug to avoid noise.

```python
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
        await logger.adebug(
            "request_timing",
            method=request.method, path=request.url.path,
            duration_ms=round(elapsed * 1000, 2),
        )
        return response
```

Use `time.perf_counter()` (monotonic), not `time.time()`. Register these in the app factory in
reverse execution order alongside `CorrelationIdMiddleware`.
