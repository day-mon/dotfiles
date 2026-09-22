---
name: codebase-design
description: Design codebase structure. Trigger whenever doing work in a codebase — adding a new feature or creating a new one. Also use for feature organization, workspace boundaries, service and repository responsibilities, splitting oversized services, or choosing language-specific libraries.
---

# Codebase Design

Recommend the smallest structural change that creates an earned boundary.

An **earned boundary** exists because code has a different runtime, dependency direction, responsibility, ownership, or reason to change — not because a template says so.

## Workflow

### 1. Inspect

Read the manifests, framework configuration, entrypoints, representative features, dependency composition, persistence code, external clients, and tests.

Complete when you can name:

- every runnable artifact;
- the dominant existing convention;
- the business features involved;
- persistence and external-system boundaries;
- the current composition root;
- the docstring style of neighboring files (grep 2–3 files before generating new modules; match their style — e.g. Sphinx `:param:` vs Google `Args:` — do not introduce a second house style).

### 2. Classify

Choose the lowest sufficient level:

- **Level 1:** cohesive files in one package
- **Level 2:** feature folders in one package
- **Level 3:** language-native workspace packages

Complete when every proposed boundary has a concrete reason.

### 3. Load the matching reference

- Level 1 or 2: read `references/feature-structure.md`
- Level 3: read `references/workspace-packages.md`
- Responsibility questions: read `references/component-roles.md`
- Oversized service: read `references/service-splitting.md`
- Language-specific library defaults: read `references/<language>/library-choices.md` when the directory exists

Load only references reached by the repository's branch.

### 4. Design

Produce a repository-specific target tree and dependency direction.

Complete when:

- every proposed file has one stated responsibility;
- every dependency crosses an explicit allowed boundary;
- no empty speculative layer remains;
- no handwritten HTTP client wraps an API that already has an official or actively maintained SDK (e.g. `openai` for the OpenAI API) — wrap or configure the SDK, never reimplement it;
- existing cohesive code is identified and preserved.

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