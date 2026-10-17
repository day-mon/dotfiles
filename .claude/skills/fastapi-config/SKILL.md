---
name: fastapi-config
description: Typed configuration for FastAPI services with pydantic-settings — a base Settings with env_prefix and nested delimiter, discriminated-union backends (sqlite|postgres, redis|memory) selected by env var, computed connection_url properties, Literal enums, and cross-field model_validator invariants. Use when adding configuration, environment variables, or swappable backends to a FastAPI service.
---

# FastAPI config

Settings are typed `pydantic-settings` models. One base sets the env conventions; subclasses
group settings by concern; swappable backends use discriminated unions.

## Base settings

```python
import pydantic_settings

class Settings(pydantic_settings.BaseSettings):
    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix="MYAPP_",
        env_nested_delimiter="__",
        case_sensitive=False,
        # .env.example ships blank values and setup copies it to .env;
        # without this, "" fails min_length and the app can't even import.
        env_ignore_empty=True,
    )
```

- `env_prefix` namespaces every variable (`MYAPP_PORT`, `MYAPP_LOG_LEVEL`).
- `env_nested_delimiter="__"` allows nested models via env, e.g. `MYAPP_DB__HOST=...`.

Subclass per concern and expose a module-level `settings` instance for import:

```python
class AppSettings(Settings):
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: typing.Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    environment: typing.Literal["development", "production"] = "development"

settings = AppSettings()
```

## File layout

```text
core/config/
├── base.py         BaseConfig only: the shared model_config
├── app.py          AppSettings + app_settings = AppSettings()
├── glean.py        GleanSettings(env_prefix="GLEAN_") + glean_settings = GleanSettings()
└── confluence.py   ConfluenceSettings(env_prefix="CONFLUENCE__") + confluence_settings = ...
```

A subclass's `model_config` merges with `BaseConfig`'s, so each file sets only its
`env_prefix`. The composition root (lifespan, worker entrypoint) imports the instance
(`from app.core.config.glean import glean_settings`) and passes it to `GleanClient.create(...)`.
Services and clients receive settings and never import them; tests construct `Settings(...)`
and pass it in. Don't thread settings through `create_app(settings)` or a `SettingsDep`.

Keep features in one class when they're cross-validated: disabled|live unions whose
validator spans several of them ("synthesis needs live Jira and conversations") stay
nested under one `Settings(AppSettings)`.

## Secrets

A required secret has no default, so a missing env var fails at import, before the app starts.
When a secret is required only in one mode, check it in a `model_validator` so it still fails at
startup, then unwrap it in a property so callers never handle `SecretStr | None`:

```python
class GleanSettings(Settings):
    mode: typing.Literal["fixture", "live"] = "fixture"
    api_token: pydantic.SecretStr | None = None

    @pydantic.model_validator(mode="after")
    def _live_needs_token(self) -> typing.Self:
        if self.mode == "live" and self.api_token is None:
            raise ValueError("GLEAN_MODE=live requires GLEAN_API_TOKEN")
        return self

    @property
    def token(self) -> str:
        if self.api_token is None:
            raise RuntimeError("token read in fixture mode")
        return self.api_token.get_secret_value()
```

## Literal enums, properties, validators

Use `Literal` for closed sets, `@property` for derived values, and a `model_validator` for
cross-field invariants.

```python
import pydantic

class AppSettings(Settings):
    environment: typing.Literal["development", "production"] = "development"
    log_type: typing.Literal["json", "normal"] = "normal"

    @property
    def reload(self) -> bool:
        return self.environment == "development"

    @property
    def is_json_logs(self) -> bool:
        return self.log_type == "json"

    @pydantic.model_validator(mode="after")
    def _json_logs_in_prod(self) -> typing.Self:
        if self.environment == "production" and self.log_type != "json":
            raise ValueError("production requires MYAPP_LOG_TYPE=json")
        return self
```

## Swappable backends — discriminated unions

For an either/or backend, model each variant separately with a `type` literal, then select by a
`discriminator` field. Each variant computes its own `connection_url` as a property — the single
source of truth, no string-building elsewhere.

```python
import pydantic

class SqliteSettings(pydantic.BaseModel):
    type: typing.Literal["sqlite"] = "sqlite"
    database: str = "db.sqlite3"

    @property
    def connection_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.database}"

class PostgresSettings(pydantic.BaseModel):
    type: typing.Literal["postgres"] = "postgres"
    host: str
    port: int = 5432
    database: str
    username: str
    password: str

    @property
    def conninfo(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def connection_url(self) -> str:
        return self.conninfo.replace("postgresql://", "postgresql+psycopg://", 1)

class DatabaseSettings(Settings):
    db: typing.Annotated[
        SqliteSettings | PostgresSettings,
        pydantic.Field(discriminator="type"),
    ] = pydantic.Field(default_factory=SqliteSettings)
    echo: bool = False
    expire_on_commit: bool = False
```

Select the variant via env: `MYAPP_DB__TYPE=postgres`, `MYAPP_DB__HOST=...`. Default to the
simplest backend (sqlite, in-memory cache) so local dev needs no config.

The same pattern fits a cache (`redis | memory`); each variant returns its own `connection_url`
(`redis://...` or `mem://`). Those URLs feed the lifespan setup in `fastapi-app-composition` and
the engine in `fastapi-sqlalchemy`.

## Rules

- One base `Settings` with `env_prefix` + `env_nested_delimiter`; subclass per concern.
- `base.py` holds only the base config; one file per concern, each ending in a
  module-level instance.
- Base config sets `env_ignore_empty=True`.
- Cross-validated feature unions stay in one class.
- Missing secrets fail at startup: required field, or a `model_validator` for mode-specific ones.
- Secrets reach callers through an unwrapping property, never `.get_secret_value()`
  scattered at call sites.
- `Literal` for enumerated options; `@property` for anything derived.
- Discriminated unions (`Field(discriminator="type")`) for swappable backends; never branch on a
  raw string field.
- Compute `connection_url` (and similar) as a property on the variant — never duplicate the
  construction logic.
- Postgres uses the psycopg 3 driver (`postgresql+psycopg`), not asyncpg; procrastinate needs it
  to defer jobs inside the app's transaction (see `fastapi-background-tasks`).
- Enforce cross-field invariants with `@model_validator(mode="after")`.
- Default to dev-friendly backends so the service runs with zero env vars locally.
