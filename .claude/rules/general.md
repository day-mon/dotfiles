---
paths:
  - "**/*.{py,ts,tsx,js,jsx,go,rs,java,kt,rb,c,cpp,h,hpp,cs,php,swift,scala}"
---

# general coding rules

language-agnostic principles. language-specific rules (python, typescript, ...)
override these where they conflict.

## don't mutate inputs or external state

functions take inputs and return outputs. they don't reach out and change their
arguments or shared/global state.

```
// bad — mutates the caller's object
applyDiscount(foo) { foo.bar -= 1 }

// good — returns a new value, leaves the input alone
applyDiscount(foo) { return { ...foo, bar: foo.bar - 1 } }
```

## prefer pure functions

same input → same output, no hidden i/o. push side effects (network, disk, db,
logging) to the edges and keep the core logic pure and easy to test.

## fail fast, guard early

validate up front and return early. avoid deep nesting — handle the bad cases
first, then let the happy path fall through unindented.

```
// good
function process(req) {
  if (!req.user) return error("no user")
  if (!req.body) return error("no body")
  // ... happy path
}
```

## name things for intent

names describe what something is *for*, not its type or how it's built.

- good: `pendingInvites`, `retryCount`, `isExpired`
- bad: `arr`, `data2`, `tmpObj`, `flagBool`

## small functions, one job

a function does one thing. if explaining it needs the word "and" or a paragraph,
split it.

## no magic values

name literals that carry meaning.

```
// bad
if (status === 3) { ... }
sleep(86400)

// good
if (status === STATUS.ARCHIVED) { ... }
sleep(ONE_DAY_SECONDS)
```

## no nonsense comments

don't narrate the obvious — the code already says *what*. comment the *why*: intent,
trade-offs, gotchas. when you document, use the language's native doc convention:

- typescript / javascript → jsdoc (`/** ... */`)
- python → google-style docstrings
- go → godoc (`// FuncName does ...`)
- rust → rustdoc (`/// ...`)
- java → javadoc (`/** ... */`)

```
// bad — narrates the obvious
i += 1 // increment i

// good — explains why
// stripe rounds half-up; mirror that so our totals reconcile with their dashboard
total = roundHalfUp(total)
```

google-style python docstring for reference:

```python
def apply_discount(price: float, pct: float) -> float:
    """Apply a percentage discount to a price.

    Args:
        price: Original price in dollars.
        pct: Discount to apply, as a fraction between 0 and 1.

    Returns:
        The discounted price, rounded to two decimal places.

    Raises:
        ValueError: If pct is outside the range [0, 1].
    """
    if not 0 <= pct <= 1:
        raise ValueError("pct must be between 0 and 1")
    return round(price * (1 - pct), 2)
```
