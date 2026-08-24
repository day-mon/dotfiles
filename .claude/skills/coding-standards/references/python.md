# Python

Apply every relevant rule to Python source.

## Naming and types

- Use the shortest name that remains clear in context. Prefer `data`, `ctx`, `err`, `idx`, and `namespace` when their meaning is unambiguous.
- Name functions with verbs or action phrases such as `fetch`, `parse_json`, and `to_dict`.
- Use `SCREAMING_SNAKE_CASE` only for true constants.
- Type every function parameter, return value, and class attribute.
- Use `T | None` and other `|` unions on Python 3.10 and later.
- Prefer early returns, f-strings, and comprehensions over `map` and `filter`.

## Immutable constants

Use immutable types for module-level collection constants.

```python
from types import MappingProxyType
from typing import Final

ALLOWED_METHODS: Final = frozenset({"GET", "POST", "PUT"})
DEFAULT_HEADERS: Final = MappingProxyType({"content-type": "application/json"})
STATUS_CODES: Final = (200, 201, 204)
```

Use a tuple instead of a list, a `frozenset` instead of a set, and `MappingProxyType` instead of a mutable dictionary.

## Assignment expressions

Use `:=` when it removes a repeated operation or makes a loop or comprehension clearer.

```python
if match := re.search(pattern, text):
    return match.group(1)

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

## Documentation

Write Google-style docstrings for public APIs or behavior whose contract is not obvious from its signature.

```python
def fetch_user(user_id: int, *, include_inactive: bool = False) -> dict[str, object] | None:
    """Retrieve a user by ID.

    Args:
        user_id: Unique user identifier.
        include_inactive: Whether to include a deleted user.

    Returns:
        User data, or None when no matching user exists.

    Raises:
        PermissionError: The caller lacks read access.
    """
```

Keep comments rare. Explain a constraint or reason, not the operation on the next line.

Before completing Python work, verify every changed signature is typed, module constants cannot be mutated, public contracts use Google-style docstrings where needed, and each comment explains why.
