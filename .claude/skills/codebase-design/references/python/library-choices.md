# Python Library Choices

Prefer these defaults; record the concrete pick in the design output and justify any deviation. Keep one default per concern.

| Concern | Default | Why |
| --- | --- | --- |
| Schema validation | `pydantic` | One model layer shared by API schemas, internal types, and config. |
| Environment config | `pydantic-settings` | Typed env parsing, invariants via `model_validator`. |
| HTTP client | `aiohttp` + `aiohttp-retry` | Fastest async client and actively maintained. |
| DI (HTTP) | FastAPI `Depends` | The framework already has DI; no container in HTTP apps. |
| DI (workers, CLI, cron) | `dishka` | Only where `Depends` can't reach; scoped providers with async teardown. |
| Queue / crons | none, then `procrastinate` | Avoid a queue until work must be durable, retried, or scheduled. Then procrastinate: Postgres is the broker, so jobs commit in the same transaction as the data. Own schema, never `public`. |
| CLI | `cyclopts` | Class-based commands in `commands/`. |
| Multi-process container | `supervisord` | Runs api + worker in one image. |
| Status / enum fields | `Literal[...]` | Including SQLAlchemy `Mapped[Literal[...]]` and pydantic fields. |

HTTP-client rule: use `aiohttp`; do not introduce a second HTTP client (`httpx`/`requests`) for ergonomics. Use the session's `ClientTimeout`; never wrap calls in `asyncio.timeout`.

## Class-based client pattern (`aiohttp` + `pydantic`)

One class per external API. Every operation funnels through a single private `_request`, the only place that knows about HTTP. Operation methods only build path/params and validate the response into pydantic models. First check whether an official SDK exists; this pattern is for APIs without one.

```python
from __future__ import annotations

from typing import Any, ClassVar, Literal, Self, TypeVar

import aiohttp
import structlog
from aiohttp.client import _RequestOptions
from aiohttp_retry import ExponentialRetry, RetryClient
from pydantic import TypeAdapter
from typing_extensions import Unpack

log = structlog.get_logger()

T = TypeVar("T")


class WidgetsClient:
    TIMEOUT_SECONDS: ClassVar[float] = 30
    RETRY_ATTEMPTS: ClassVar[int] = 3

    def __init__(self, *, base_url: str, token: str) -> None:
        session = aiohttp.ClientSession(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS),
            raise_for_status=True,
            trace_configs=[self._request_logging_trace()],
        )
        self.session = RetryClient(
            client_session=session,
            retry_options=ExponentialRetry(attempts=self.RETRY_ATTEMPTS),
        )

    @classmethod
    def create(cls, settings: WidgetsSettings) -> Self:
        return cls(base_url=settings.base_url, token=settings.token)

    async def aclose(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    @staticmethod
    def _request_logging_trace() -> aiohttp.TraceConfig:
        trace = aiohttp.TraceConfig()

        async def on_request_end(
            _session: aiohttp.ClientSession,
            _ctx: Any,
            params: aiohttp.TraceRequestEndParams,
        ) -> None:
            log.info(
                "http_request",
                method=params.method,
                url=str(params.url),
                status=params.response.status,
            )

        trace.on_request_end.append(on_request_end)
        return trace

    async def _request(
        self,
        *,
        method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        model: type[T],
        **request_opts: Unpack[_RequestOptions],
    ) -> T:
        async with self.session.request(method=method, url=path, **request_opts) as response:
            data = await response.json()
        return TypeAdapter(model).validate_python(data)

    async def get_widget(self, *, widget_id: str) -> Widget:
        return await self._request(method="GET", path=f"/widgets/{widget_id}", model=Widget)

    async def list_widgets(self, *, page_size: int = 50) -> list[Widget]:
        return await self._request(
            method="GET",
            path="/widgets",
            params={"pageSize": page_size},
            model=list[Widget],
        )
```

Rules for this shape:

- Every argument after `self` is keyword-only.
- `_request` validates through `TypeAdapter(model)`: pass `Widget`, `list[Widget]`, or `dict[str, Widget]`. No wrapper `BaseModel` just to hold a list.
- `**request_opts` is typed as `Unpack[_RequestOptions]`, so `params=`, `json=`, `headers=` are type-checked without redeclaring aiohttp's arguments.
- Public methods never touch `aiohttp` types.
- Constants are `ClassVar`s, helpers are `@staticmethod`s, construction from settings is `create()`.
- `raise_for_status=True` on the session. Errors propagate to the app's global handler; the client does not catch or wrap them.
- Session lifecycle is explicit (`aclose` / async context manager), owned by a DI provider. Construct only where an event loop is running.
- No docstrings; names and types carry the contract.

## Configuration (`pydantic-settings`)

One `BaseSettings` subclass per component. Never hand-roll `os.environ` parsing.

```python
from pathlib import Path
from typing import Final, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WidgetsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    tenant: str = Field(default="acme", validation_alias="WIDGETS_TENANT")
    token: str = Field(validation_alias="WIDGETS_TOKEN")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cache_dir: Path = Field(
        default=Path.home() / ".cache" / "widgets",
        validation_alias="WIDGETS_CACHE",
    )

    @property
    def base_url(self) -> str:
        return f"https://{self.tenant}.example.com/api"


settings: Final = WidgetsSettings()
```

Rules for this shape:

- `frozen=True` + `extra="ignore"`.
- Required values have no default, so a missing env var fails at startup.
- Let pydantic coerce types (`int`, `Path`, `Literal`). Never `int(os.environ.get(...) or default)`.
- Derived values are `@property`s, never stored fields.
- Define `settings: Final = Settings()` at module level. Do not use `@lru_cache def get_settings()`.
- Only the composition root (lifespan, worker entrypoint) imports the instance and passes it to `create(settings)`. Services, clients, and libraries receive settings; they never import them.
- Tests construct `Settings(...)` and pass it to `create()`; no monkeypatching the module instance.
