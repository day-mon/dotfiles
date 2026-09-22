# Python Library Choices

Prefer these defaults; record the concrete pick in the design output and justify any deviation. Other languages get sibling directories (`references/<language>/library-choices.md`); keep one default per concern.

## Class-based client pattern (`aiohttp` + `pydantic`)

One class per external API. Every operation funnels through a single private `_request`, which is the only place that knows about HTTP: literal method set, shared request options, `raise_for_status`, trace-config logging, timeouts, retry. Operation methods only build path/params and validate the response into pydantic models.

```python
from __future__ import annotations

import logging
from typing import Any, Literal, TypeVar

import aiohttp
from aiohttp.client import _RequestOptions
from typing_extensions import Unpack
from aiohttp_retry import ExponentialRetry, RetryClient
from pydantic import TypeAdapter

log = logging.getLogger(__name__)

Method = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
T = TypeVar("T")


class WidgetsClient:
    """Client for the Widgets API.

    One class per external API; owns its session and closes it explicitly.
    Construct clients inside a running event loop (aiohttp requires one),
    i.e. at the async composition root — a FastAPI lifespan or
    ``async def main``, never at module scope.

    :attribute session: The retry-wrapped aiohttp session used for all requests.
    """

    def __init__(self, *, base_url: str, token: str, timeout_seconds: float = 30) -> None:
        """Initialize the client and its session.

        :param base_url: API base URL, e.g. ``https://api.example.com``.
        :param token: Bearer token sent on every request.
        :param timeout_seconds: Total per-request timeout.
        """
        session = aiohttp.ClientSession(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=aiohttp.ClientTimeout(total=timeout_seconds),
            raise_for_status=True,  # surfaces as aiohttp.ClientResponseError
            trace_configs=[self._request_logging_trace()],
        )
        # RetryClient wraps the session; exponential backoff on 5xx/timeouts.
        self.session = RetryClient(
            client_session=session, retry_options=ExponentialRetry(attempts=3)
        )

    async def aclose(self) -> None:
        """Close the underlying session."""
        await self.session.close()

    @staticmethod
    def _request_logging_trace() -> aiohttp.TraceConfig:
        """Build the trace config that logs requests.

        :returns: A trace config logging method, URL, and status once per response.
        """
        trace = aiohttp.TraceConfig()

        async def on_request_end(
            _session: aiohttp.ClientSession,
            _ctx: Any,
            params: aiohttp.TraceRequestEndParams,
        ) -> None:
            log.info("http %s %s -> %s", params.method, params.url, params.response.status)

        trace.on_request_end.append(on_request_end)
        return trace

    async def __aenter__(self) -> WidgetsClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    # --- the only method that knows about HTTP ---

    async def _request(
        self,
        *,
        method: Method,
        path: str,
        model: type[T] | None = None,
        **request_opts: Unpack[_RequestOptions],
    ) -> T:
        """Send one request and validate the JSON body.

        The only method that knows about HTTP; operations call this.

        :param method: HTTP method.
        :param path: Path relative to ``base_url``.
        :param model: Pydantic model (or container like ``list[Widget]``) to
            validate the response into. Omit for endpoints whose body is ignored.
        :param request_opts: Extra ``aiohttp`` options (``params``, ``json``,
            ``data``, ``headers``, ...).
        :returns: The response body validated into ``model``, or the raw JSON
            when ``model`` is omitted.
        :raises aiohttp.ClientResponseError: Non-2xx status (``raise_for_status``).
        :raises pydantic.ValidationError: Body does not match ``model``.
        """
        async with self.session.request(method=method, url=path, **request_opts) as response:
            data = await response.json()
        if model is None:
            return data
        return TypeAdapter(model).validate_python(data)

    # --- operations: path + expected model only, every arg keyword-only ---

    async def get_widget(self, *, widget_id: str) -> Widget:
        """Fetch one widget.

        :param widget_id: The widget's id.
        :returns: The widget.
        """
        return await self._request(method="GET", path=f"/widgets/{widget_id}", model=Widget)

    async def list_widgets(self, *, page_size: int = 50) -> list[Widget]:
        """List widgets.

        :param page_size: Maximum number of widgets to return.
        :returns: A page of widgets.
        """
        return await self._request(
            method="GET",
            path="/widgets",
            params={"pageSize": page_size},
            model=list[Widget],
        )
```

Rules for this shape:

- Every argument after `self` is keyword-only, on `__init__`, operations, and `_request` itself.
- `_request` auto-validates through `TypeAdapter(model)` — pass `Widget` for one object, `list[Widget]` or `dict[str, Widget]` for containers; no wrapper `BaseModel` just to hold a list. Omit `model=` for endpoints whose body is ignored.
- `**request_opts` is typed as `Unpack[_RequestOptions]` from `aiohttp.client` — `params=`, `json=`, `data=`, `headers=` etc. get full type checking without redeclaring aiohttp's argument list. It is a private name but stable; if that ever bothers you, alias it once in the client module and import from there.
- `_request` is private; public methods never touch `aiohttp` types.
- Docstrings are reStructuredText/Sphinx style (`:param:`, `:returns:`, `:raises:`).
- `raise_for_status=True` on the session, not per call; translate `ClientResponseError` at the service layer, not here.
- Session lifecycle is explicit (`aclose` / async context manager), wired at the composition root. The session is built eagerly in `__init__` — but only construct the client where a loop is running.
- The trace config is a `@staticmethod` on the client class: per-client logging behavior travels with the class, no module-level helpers to import.
- First check whether an official SDK exists (see SKILL.md step 4); this pattern is for APIs without one.

| Concern | Default | Why |
| --- | --- | --- |
| Schema validation | `pydantic` | One model layer shared by API schemas, internal types, and config. |
| Environment config | `pydantic-settings` | Typed env parsing (`env_prefix`, nested delimiter), invariants via `model_validator`. |
| HTTP client | `aiohttp` | Fastest async client by a wide margin and actively maintained; pairs with `aiohttp-retry` for backoff. |

HTTP-client rule: use `aiohttp`; do not introduce a second HTTP client (`httpx`/`httpx2`/`requests`) for ergonomics. When a performance number matters, re-benchmark in place — published comparisons disagree between 5% and 35x depending on pooling, concurrency, and whether bodies are read (see encode/httpx#3215 for how often people get this wrong).

## Configuration (`pydantic-settings`)

One `BaseSettings` subclass per component. Never hand-roll `os.environ` parsing — no `int(os.environ.get(...))` guards or module-scope constants derived from env.

```python
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WidgetsConfig(BaseSettings):
    """Runtime knobs, each sourced from its environment variable."""

    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    tenant: str = Field(default="acme", validation_alias="WIDGETS_TENANT")
    cdp_port: int = Field(default=9222, validation_alias="WIDGETS_CDP_PORT")
    cache_dir: Path = Field(
        default=Path.home() / ".cache" / "widgets",
        validation_alias="WIDGETS_CACHE",
    )
    optional_file: Path | None = Field(default=None, validation_alias="WIDGETS_FILE")

    @property
    def api_base(self) -> str:
        return f"https://{self.tenant}.example.com/api"


def load_config() -> WidgetsConfig:
    """Read the environment once and return an immutable settings object."""
    return WidgetsConfig()
```

Rules for this shape:

- `frozen=True` + `extra="ignore"`: settings are immutable, and unrelated env vars never crash startup.
- Explicit `validation_alias` per field when a project mixes env prefixes (legacy names, third-party names like `DIA_*`); only use `env_prefix` when every variable shares one prefix.
- Let pydantic do type coercion (`int`, `Path`, `Literal` unions); validation errors at construction are the only checking the config needs. Integer fields must never use pattern `int(os.environ.get(...) or default)`.
- Derived values (URLs, file paths under `cache_dir`) are read-only `@property`s on the settings class, never stored fields.
- Single-process tools and scripts: declare `config: Final = WidgetsConfig()` in the config module and import the singleton; env parsing at import time is the desired fail-fast, and pydantic-settings already supports per-construction overrides (`WidgetsConfig(tenant="acme")`) for tests. App servers with a lifespan: construct at the composition root and pass the instance down instead.
- Do not call `WidgetsConfig()` inside libraries — receive the settings object.
