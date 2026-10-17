---
name: damon-mode
description: Index and precedence rules for Damon's engineering skills. Read first on any coding, design, review, debugging, refactoring, or skill-editing task to find which skill owns the rule, which principle applies, and how conflicts between skills resolve.
---

# Damon mode

This file routes. The skills it names own the details; read the owner before applying or quoting a rule. Skills live at `../<name>/SKILL.md` from this file.

## Precedence

When two sources disagree, the higher one wins:

1. The user's instruction in this session
2. This hub's conflict rulings (below)
3. Framework skills (`fastapi-*`)
4. `coding-standards` language references, then its universal rules
5. `codebase-design`
6. Principles (`principle-*`)

Principles explain judgment. Concrete rules live in the skills above them. A principle never overrides a concrete rule; it tells you what to do where no rule exists.

## Who owns which rule

Each rule lives in one file. Every other file links to it. To change a rule, edit its owner.

| Rule | Owner |
|---|---|
| Comments and docstrings, naming, guard clauses, errors, logging, constants as `ClassVar` | `coding-standards` |
| Python specifics (types, `Literal`, `:=`, pydantic validation, no `assert`) | `coding-standards/references/python.md` |
| Tests: factories, real database, fakes one layer up | `coding-standards/references/testing.md` |
| Structure levels, placement table, DI (`Depends` first, Dishka for workers/CLI) | `codebase-design` |
| Library defaults (aiohttp, pydantic-settings, procrastinate, Dishka) and the client class shape | `codebase-design/references/python/library-choices.md` |
| Settings, secrets, discriminated-union backends | `fastapi-config` |
| App factory, lifespan, middleware, error handlers | `fastapi-app-composition` |
| `Depends` aliases | `fastapi-dependencies` |
| Routes and path operations | `fastapi-routing` |
| `api/v<n>/<domain>/` slice layout | `fastapi-module-structure` |
| FastAPI client wiring | `fastapi-http-clients` |
| Models, mixins, sessions | `fastapi-sqlalchemy` |
| Migrations and drift checks | `fastapi-alembic` |
| Queues and periodic jobs | `fastapi-background-tasks` |
| Response shape for the reader | `i-have-adhd` |
| Prose for others (Slack, docs, PRs) | `writing`, then `unslop` |
| PR review labels and replies | `pr-review` |

## Conflict rulings

- **Asking vs proceeding.** Proceed on reversible work (`principle-never-block-on-the-human`). Confirm first before moving or deleting files in a restructure, schema migrations, force pushes, and external messages. `codebase-design` step 0 stands: show the target tree, then wait.
- **Refactor vs rewrite.** A structural refactor moves code in behavior-preserving steps (`codebase-design/references/service-splitting.md`). A planned rewrite with phase boundaries may break intermediate states (`principle-outcome-oriented-execution`). Neither leaves compatibility shims behind (`principle-migrate-callers-then-delete-legacy-apis`).
- **One default vs prototypes.** Use the documented default for each concern. Prototype competing designs only for a decision no skill covers yet, then record the winner in its owner.
- **Mock payloads.** Asserting the payload an external service receives is behavior (`principle-test-behavior-not-implementation`). Asserting calls to internal collaborators is not (`testing.md`).
- **Alembic docstrings.** Migration files keep Alembic's revision docstring; it is the one docstring exception.

## Principles: when each applies

Read the leaf in full before citing it.

**Before writing code**
- `principle-foundational-thinking`: choosing core types and data structures.
- `principle-model-the-domain`: stateful logic, or a growing if/else chain.
- `principle-type-system-discipline`: designing types and signatures.
- `principle-boundary-discipline`: wiring validation, errors, framework adapters.
- `principle-redesign-from-first-principles`: fitting a new requirement into an existing design.

**While changing code**
- `principle-laziness-protocol`: tempted to add an abstraction or layer.
- `principle-subtract-before-you-add`: sequencing an addition or refactor.
- `principle-minimize-reader-load`: code that is hard to trace.
- `principle-migrate-callers-then-delete-legacy-apis`: replacing an internal API.
- `principle-outcome-oriented-execution`: planned rewrites with phase boundaries.
- `principle-sequence-verifiable-units`: multi-step work, stacking commits and PRs.
- `principle-build-the-lever`: any non-trivial edit, migration, or check.
- `principle-make-operations-idempotent`: anything that runs amid crashes, restarts, retries.
- `principle-separate-before-serializing-shared-state`: concurrent writers.

**Verifying and debugging**
- `principle-prove-it-works`: before declaring done.
- `principle-test-behavior-not-implementation`: writing or keeping a test.
- `principle-fix-root-causes`: debugging.
- `principle-attack-the-premise`: two fixes sharing one premise both failed.
- `principle-explain-the-number`: before reporting a measured number (procedure: `benchmark-checklist`).

**Working style**
- `principle-never-block-on-the-human`: tempted to ask on reversible work (see ruling above).
- `principle-guard-the-context-window`: large outputs, long files, fan-out.
- `principle-encode-lessons-in-structure`: writing the same instruction twice.

## Workflow skills

- `correct`: the same mistake keeps coming back; make it impossible.
- `reflect`: end of a session; route learnings into the owning skill.
- `unslop`: final pass on any prose.
- `benchmark-checklist`: before acting on a perf number.

## Keeping skills consistent

- Run `uv run damon-mode/scripts/check_skills.py` from the skills root after editing any skill listed here. It fails on broken skill references, unindexed principles, banned stale patterns, and Python examples that don't parse.
- A new rule goes in its owner. If no owner fits, add a row to the table above first.
- A new principle or workflow skill gets a line in this file, or the check fails.

`principle-*`, `correct`, `reflect`, `unslop`, and `benchmark-checklist` are adapted from cursor/plugins `pstack` (MIT, Lauren Tan, commit `101b274`); see `references/pstack-LICENSE`.
