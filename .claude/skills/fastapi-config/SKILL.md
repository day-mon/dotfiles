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
    def _no_reload_in_prod(self) -> "AppSettings":
        if self.environment == "production" and self.reload:
            raise ValueError("reload cannot be enabled in production")
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
    def connection_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

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
- `Literal` for enumerated options; `@property` for anything derived.
- Discriminated unions (`Field(discriminator="type")`) for swappable backends; never branch on a
  raw string field.
- Compute `connection_url` (and similar) as a property on the variant — never duplicate the
  construction logic.
- Enforce cross-field invariants with `@model_validator(mode="after")`.
- Default to dev-friendly backends so the service runs with zero env vars locally.
