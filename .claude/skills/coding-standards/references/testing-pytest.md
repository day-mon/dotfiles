# pytest

Apply to Python tests. Read `testing.md` first; this file says how to do it the pytest way. Targets pytest 9, pytest-asyncio 1.x, polyfactory 3, Starlette 1.x (`httpx2`).

## Configuration

Use pytest 9's native TOML table, not `[tool.pytest.ini_options]`. Pin pytest in the lockfile, then turn on strict mode.

```toml
[tool.pytest]
minversion = "9.0"
testpaths = ["tests"]
addopts = ["-ra"]
strict = true
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
filterwarnings = ["error"]
```

- `strict = true` turns unknown markers, unknown config keys, duplicate parametrize ids, and passing `xfail`s into errors.
- `asyncio_mode = "auto"` means no `@pytest.mark.asyncio` on every test.
- One event loop for the session, so a session-scoped engine and the tests that use it share a loop.
- `filterwarnings = ["error"]` makes deprecations fail now instead of breaking the next upgrade.

## Layout

```text
tests/
├── conftest.py              global fixtures: app, client, database, session, fakes
├── factories.py             polyfactory factories + SQLALCHEMY_FACTORIES
├── fakes.py                 fake services and clients for one-layer-up tests
├── api/v1/weather/
│   ├── conftest.py          fixtures only this domain's tests share
│   └── test_routes.py
├── services/test_weather.py
└── clients/test_open_meteo.py
```

- Tests mirror `src/` and live in `tests/`, never next to the code.
- Name tests after the behavior: `test_unknown_city_returns_404`, not `test_get_weather_2`.

## conftest.py holds the fixtures

Fixtures live in `conftest.py`, not in test files. pytest discovers them by directory, so never import a fixture.

- `tests/conftest.py`: everything more than one area uses (settings, app client, database, session, fakes).
- `tests/<area>/conftest.py`: fixtures only that directory's tests share. A nested conftest can override a parent fixture by defining one with the same name.
- A test file holds tests. A fixture goes in the test file only when exactly one test uses it and it is a few lines; move it to the nearest conftest the moment a second file needs it.

```python
# tests/conftest.py
from collections.abc import AsyncIterator, Iterator

import httpx2
import pytest
from alembic import command
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from app.api.v1.weather.routes import get_weather_service
from app.core.config import Settings
from app.main import create_app
from tests.factories import SQLALCHEMY_FACTORIES
from tests.fakes import FakeWeather
from tests.migrations import alembic_config


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:17", driver="psycopg") as pg:
        url = pg.get_connection_url()
        command.upgrade(alembic_config(url), "head")
        yield url


@pytest.fixture(scope="session")
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(database_url)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        transaction = await conn.begin()
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as session:
            for factory in SQLALCHEMY_FACTORIES:
                monkeypatch.setattr(factory, "__async_session__", session)
            yield session
        await transaction.rollback()


@pytest.fixture
def settings() -> Settings:
    return Settings(open_meteo_base_url="http://open-meteo.test", tracked_cities=("Berlin",))


@pytest.fixture
def weather() -> FakeWeather:
    return FakeWeather()


@pytest.fixture
async def client(weather: FakeWeather) -> AsyncIterator[httpx2.AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_weather_service] = lambda: weather
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
```

- Setup and teardown live in one `yield` fixture. Code after `yield` always runs, even when the test fails.
- Scope: `session` for expensive and immutable (container, engine); `function` (the default) for anything a test can change. Never widen a mutable fixture's scope to save time.
- Build settings with `Settings(...)` in a fixture and pass them in. Never `monkeypatch.setenv` app settings; use `monkeypatch` only for process-level state you don't own.
- Replace FastAPI dependencies with `app.dependency_overrides`, never `mock.patch` on a route's imports.
- Use a fixture factory when a test needs several variants: the fixture returns a function (`make_user(role="admin")`).
- `autouse=True` only for setup every test in that directory truly needs. An autouse fixture in the root conftest runs for every test in the suite.
- Built-ins first: `tmp_path`, `monkeypatch`, `capsys`. For structlog output use `structlog.testing.capture_logs()`.
- Check where a fixture came from with `uv run pytest --fixtures-per-test path/to/test.py`.

The `session` fixture rolls back after every test, so each test starts from an empty database. `join_transaction_mode="create_savepoint"` lets code under test call `commit()` while the test still rolls everything back. Never `create_all()` in tests; the migrations are what ship. Import `PostgresContainer` from `testcontainers.community.postgres`; the old `testcontainers.postgres` path is deprecated and fails under `filterwarnings = ["error"]`.

## Plain functions and plain `assert`

```python
async def test_unknown_city_returns_404(client: httpx2.AsyncClient, weather: FakeWeather) -> None:
    weather.cities = {}

    response = await client.get("/v1/weather/Atlantis")

    assert response.status_code == 404
    assert response.json() == {"message": "City not found: Atlantis"}
```

- Plain functions, not `unittest.TestCase` classes; plain `assert`, never `self.assertEqual`. pytest rewrites `assert` to show both sides.
- Arrange, act, assert, separated by one blank line each. No `# arrange` comments.
- No `if`, `for`, or `try` in a test body. A loop over cases is `parametrize`; a branch means two tests.
- Compare whole values (`== {...}`, `== Model(...)`) instead of picking fields one by one, unless the other fields are noise.
- Floats and datetimes: `pytest.approx` (pytest 9 accepts `datetime` with a `timedelta` tolerance).
- Type every test and fixture signature like app code.

## Parametrize

```python
@pytest.mark.parametrize(
    ("city", "status"),
    [
        pytest.param("Berlin", 200, id="tracked-city"),
        pytest.param("Lisbon", 200, id="untracked-city-looked-up"),
        pytest.param("Atlantis", 404, id="unknown-city"),
    ],
)
async def test_city_lookup_status(client: httpx2.AsyncClient, city: str, status: int) -> None:
    response = await client.get(f"/v1/weather/{city}")

    assert response.status_code == status
```

- `argnames` as a tuple, every case a `pytest.param` with an `id` describing the case. Strict mode rejects duplicate ids.
- Pass a list or tuple, never a generator (deprecated in pytest 9).
- Use `subtests` only when the cases aren't known until runtime (files on disk, rows from a query).

## Errors

```python
with pytest.raises(CityNotFoundError):
    await service.current_temperature("Atlantis")
```

The error type is the contract. Add `match=` only when callers read the message, and anchor it.

## Factories

`tests/factories.py` holds every factory. Use polyfactory: `ModelFactory` for pydantic models, `SQLAlchemyFactory` for ORM models. Put validity rules in the factory; tests override only the field they're about.

```python
# tests/factories.py
class PlaceFactory(ModelFactory[Place]):
    latitude = Use(lambda: 52.52)
    longitude = Use(lambda: 13.40)


class RunFactory(SQLAlchemyFactory[Run]):
    __persistence_method__ = SQLAlchemyPersistenceMethod.FLUSH
    __set_primary_key__ = False
    outcome = "pending"


SQLALCHEMY_FACTORIES = (RunFactory,)
```

- List every `SQLAlchemyFactory` in `SQLALCHEMY_FACTORIES`; the conftest `session` fixture binds them all to the test's session.
- `await RunFactory.create_async(outcome="failed")` inserts one row inside the test's transaction; `.build()` makes one in memory.
- `FLUSH`, not the default `COMMIT`, so the rollback undoes it. Pass the enum, not the string `"flush"`, which silently fails.

## Faking, in order of preference

1. **Inject a fake** one layer up (`tests/fakes.py`), typed like the real thing.
2. **Fake the network edge** when testing the client itself: `aioresponses` for aiohttp. Assert on the request the upstream receives and on the parsed model.
3. **`monkeypatch.setattr`** for a boundary you don't own (a clock, `uuid`).
4. **`mocker` (pytest-mock)** only when a call itself is the contract. Always `autospec=True`.

Never `unittest.mock.patch` an internal function of the module under test. For time, use `time_machine.travel(...)`, not a patched `datetime`.

## Async

- `async def test_...` just works in auto mode; never call `asyncio.run` in a test.
- Async fixtures are plain `@pytest.fixture async def`.
- Don't `asyncio.sleep` to wait for background work; await the task, or call the job's single-run method directly.

## Running

- `uv run pytest` locally and in CI. Same command, same config.
- `-x --lf` while iterating; `-n auto` (pytest-xdist) once tests are independent.
- A flaky test is a bug. Fix it or delete it; don't add `pytest-rerunfailures`.

## Before finishing

Every test is a plain function with a behavior name, has no branches or loops, gets its fixtures from a `conftest.py`, builds inputs with factories, and passes under `strict = true` with warnings as errors.
