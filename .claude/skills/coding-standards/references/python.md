# Python

Apply every relevant rule to Python source.

## Naming and types

- Use the shortest name that remains clear in context. Prefer `data`, `ctx`, `err`, `idx`, and `namespace` when their meaning is unambiguous.
- Name functions with verbs or action phrases such as `fetch`, `parse_json`, and `to_dict`.
- Use `SCREAMING_SNAKE_CASE` only for true constants.
- Type every function parameter, return value, and class attribute.
- Use `T | None` and other `|` unions on Python 3.10 and later.
- Prefer early returns, f-strings, and comprehensions over `map` and `filter`.

## Constants and helpers

Constants live on the owning class as `ClassVar`s. Helpers are `@staticmethod`s or `@classmethod`s. Construction from settings is `create()`. Module-level only when several classes share them.

```python
from types import MappingProxyType
from typing import ClassVar


class JiraClient:
    ALLOWED_METHODS: ClassVar = frozenset({"GET", "POST"})
    DEFAULT_HEADERS: ClassVar = MappingProxyType({"content-type": "application/json"})
```

Use immutable types: a tuple instead of a list, a `frozenset` instead of a set, and `MappingProxyType` instead of a mutable dictionary.

Use `Literal[...]` for fixed sets of values (statuses, HTTP methods, schema versions like `Literal[1, 2] = 2`).

## Assignment expressions

Use `:=` when it removes a repeated operation or makes a loop or comprehension clearer.

```python
if match := re.search(pattern, text):
    return match.group(1)

if (row := await self.repository.detail(job_id)) is None:
    raise RunNotFoundError

while chunk := file.read(8192):
    process(chunk)
```

Use a normal assignment when the expression gains nothing from being inline.

## Parameter boundaries

Use `/` when callers should not depend on a parameter name. Use `*` when optional settings or boolean flags should be explicit at the call site.

```python
def parse_json(data: bytes | str, /, *, strict: bool = True) -> dict[str, object]:
    ...


def connect(
    host: str,
    port: int,
    *,
    timeout: int = 30,
    retries: int = 3,
) -> Connection:
    ...
```

## Validation

Let pydantic validate. Use `@validate_call`, `model_validator`, and `@property` instead of manual checks in function bodies. Compare objects with pydantic models, never with `json.dumps(..., sort_keys=True)`. No `getattr` or `cast` to dodge typing.

## Errors and logging

Raise subclasses of the app's root `AppError`, which carries `status_code` and `message`. Do not catch to re-raise or wrap. Log through `structlog.get_logger()` with an event name and keyword fields (`log.info("job_failed", task=name, attempt=n)`), never `logging.getLogger` with `%s` formatting. Use `log.exception(...)` for tracebacks. Never format error chains into strings.

No `assert` in app code: `python -O` strips it. Narrow types with an explicit check or a better type, and enable ruff `S101` outside tests.

## Documentation

No docstrings or comments by default. If the repository requires docstrings, match its existing style.

Before completing Python work, verify every changed signature is typed, constants live on their class and cannot be mutated, validation lives in pydantic, and no comment restates the code.
