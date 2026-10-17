---
name: codebase-design
description: Design codebase structure. Trigger whenever doing work in a codebase — adding a new feature or creating a new one. Also use for feature organization, workspace boundaries, service and repository responsibilities, splitting oversized services, or choosing language-specific libraries.
---

# Codebase Design

Recommend the smallest structural change that creates an earned boundary.

An **earned boundary** exists because code has a different runtime, dependency direction, responsibility, ownership, or reason to change — not because a template says so.

## Workflow

### 0. Ground rules

- When the user asks a question or says "just a discussion", answer it. Do not edit files.
- Show the target tree and dependency rules, then wait for approval before moving any file.

### 1. Inspect

Read the manifests, framework configuration, entrypoints, representative features, dependency composition, persistence code, external clients, and tests.

Complete when you can name:

- every runnable artifact;
- the dominant existing convention;
- the business features involved;
- persistence and external-system boundaries;
- the current composition root;
- the repo's comment policy (default: no comments, see coding-standards).

### 2. Classify

Choose the lowest sufficient level:

- **Level 1:** cohesive files in one package
- **Level 2:** layered folders in one package (see the placement table in `references/feature-structure.md`)
- **Level 3:** workspace with `apps/` (runnables) and `packages/` (one capability each)

Complete when every proposed boundary has a concrete reason.

### 3. Load the matching reference

- Level 1 or 2: read `references/feature-structure.md`
- Level 3: read `references/workspace-packages.md`
- Responsibility questions: read `references/component-roles.md`
- Oversized service: read `references/service-splitting.md`
- Language-specific library defaults: read `references/<language>/library-choices.md` (`python/`, `typescript/`)

Load only references reached by the repository's branch.

### 4. Design

Produce a repository-specific target tree and dependency direction.

Complete when:

- every proposed file maps to exactly one row of the placement table;
- each service, client, and repository class has its own file;
- composition goes through the framework's DI when one exists (FastAPI `Depends`, Nest providers); Dishka only for runnables without one (workers, CLI, cron); no `build_x()` free functions beyond the dependency functions the framework requires;
- no package is named `core`, `common`, or `shared`;
- every dependency crosses an explicit allowed boundary;
- no empty speculative layer remains;
- no handwritten HTTP client wraps an API that already has an official or actively maintained SDK (e.g. `openai` for the OpenAI API) — wrap or configure the SDK, never reimplement it;
- existing cohesive code is identified and preserved.

### Design principles

Apply these when they fit the repository; they are defaults, not mandates.

- **Store data in the shape you query it.** Structure anything you filter, join, or count. Keep opaque blobs only for verbatim snapshots. Map between external contracts and storage in one place, with a round-trip test.
- **Code that runs in different contexts doesn't import across them.** Only the composition root joins them, and a tool (import linter, dependency rules) enforces the boundary rather than convention.
- **One place declares what runs and when.** Prefer an explicit registry over discovery or scattered lists.
- **Automatic recovery is bounded.** After a fixed number of attempts, failure is visible and a person decides; no silent retry loops.
- **Escape hatches need deliberate opt-in.** A missing or default setting must never disable a safety check; require an explicit flag in an explicit environment.

### 5. Plan the migration

Map existing files to the target structure in behavior-preserving steps.

Complete when each step has a validation command or observable result.

## Output

Return:

1. Current pressure points
2. Selected level and evidence
3. Target structure
4. Dependency rules
5. Migration sequence
6. Cohesive code that should remain unchanged