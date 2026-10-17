# Testing

Apply to tests in any language. Framework references override these rules: `testing-pytest.md` for Python, `testing-vitest.md` for TypeScript and React.

## Test behavior that matters

- Each test states an invariant the code must keep: an outcome, a rollback, idempotency, a permission boundary, an ordering. Delete tests that only prove the code ran or that restate the implementation.
- Prefer one test per rule with parameterized cases over many near-copies.
- When the same logic runs two ways (in memory and in a query, client and server), test that both agree.

## Build inputs with factories

- Use a factory library (factory_boy, fishery, or the ecosystem equivalent) for models and contract objects. Override only the fields the test is about.
- Factories encode the domain's validity rules so every built object is valid by default.
- Never hand-assemble large dicts or mocks to stand in for typed objects.

## Use real dependencies at the boundary being tested

- Run persistence code against the real database engine (testcontainers or a disposable instance) with real migrations applied. Engine-specific SQL, constraints, and locking only show up there.
- Mock one layer above the unit under test: test a service with a fake repository, a route with a fake service. Never mock the database driver or HTTP transport to test business logic.
- Never assert on generated SQL strings or call arguments when the result can be asserted instead.
- Return correctly typed values from fakes; a generic mock where a typed result belongs hides contract drift.

## Parameterize

Use the framework's parameterization (`pytest.mark.parametrize` with `pytest.param(..., id=...)`, `test.each`) for variations of one rule. Ids describe the case, not the values.

## Keep tests independent

- A test leaves no data behind. Clean up in a fixture, not at the end of the test body.
- Tests that count rows start from a known empty state.
- Shared expensive setup (a database container) is session-scoped; mutable state is per-test.
