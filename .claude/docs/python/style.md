# python style guide

## naming

- **variables**: short, one-word, informative. prefer context over verbosity.
  - good: `data`, `ctx`, `err`, `idx`, `pwd`, `ns`
  - bad: `user_data_dictionary`, `temporary_index_variable`
- **functions**: verb or action phrase, lowercase
  - good: `fetch()`, `parse_json()`, `to_dict()`
- **constants**: all caps for true constants only
  - good: `MAX_RETRIES`, `DEFAULT_TIMEOUT`

## walrus operator

use `:=` for assignment expressions where it eliminates redundant calls or improves flow.

```python
# good - eliminates second lookup
if match := re.search(pattern, text):
    return match.group(1)

# good - loop with side effect
while chunk := file.read(8192):
    process(chunk)

# good - comprehension filter
results = [y for x in items if (y := transform(x)) > 0]

# typed example
from typing import match

def extract_id(text: str, pattern: str) -> str | None:
    if m := re.search(pattern, text):
        return m.group(1)
    return none

# bad - no benefit over simple assignment
x := 5  # use x = 5
```

## positional-only and keyword-only args

use `*` and `/` intentionally to constrain call patterns.

```python
# / for positional-only ( cleaner api, prevents name coupling)
def parse_json(data: bytes | str, /, strict: bool = true) -> dict:
    """data is positional-only; strict can be positional or keyword."""
    ...

# * for keyword-only (clarity at call site)
def connect(host: str, port: int, *, timeout: int = 30, retries: int = 3) -> connection:
    """host/port are positional; timeout/retries must be named."""
    ...

# combined
def log(msg: str, /, level: str = "info", *, stream: file | none = none) -> none:
    """msg: positional-only
    level: positional or keyword
    stream: keyword-only
    """
    ...
```

use positional-only when:
- arg name is an implementation detail
- function is mathematical or operator-like

use keyword-only when:
- bool flags that read poorly positionally
- optional config that should be explicit

## docstrings (google style)

```python
def fetch_user(user_id: int, *, include_inactive: bool = False) -> dict | None:
    """retrieve a user by id.

    args:
        user_id: the unique identifier for the user.

    keyword args:
        include_inactive: whether to return users marked as deleted.
            defaults to false.

    returns:
        user data as a dict, or none if not found.

    raises:
        permissionerror: if caller lacks read access.
    """
```

## comments

avoid inline comments. code should speak. when you must comment, write like a human.

```python
# bad
x = x + 1  # increment x by 1

# acceptable
x = x + 1  # account for fencepost

# good - no comment needed
x = x + 1

# bad - robotic
# check if user is authenticated
if user.authenticated:

# good - explains why, not what
# guests bypass rate limiting for internal health checks
if user.authenticated:
```

## general

- lowercase for everything except classes and constants
- **always use types** — function signatures, return values, class attrs. use `|` for unions (py 3.10+).
- prefer early returns over nested ifs
- f-strings over `.format()` or `%`
- list/dict comprehensions over `map()`/`filter()`
