# typescript tooling

## package manager

use `bun`. for running one-off tools, prefer `bunx --bun` or `bunx` over `npx`.

```bash
# good — uses bun runtime
bunx --bun vite
bunx --bun tsc --noEmit

# acceptable — falls back to node if needed
bunx eslint .

# avoid — npx uses node
npx vite
```

## linting and formatting

use **biome** alongside whatever the repo already uses. biome is fast and catches things others miss.

```bash
# check with biome first
bunx --bun @biomejs/biome check .

# format
bunx --bun @biomejs/biome format --write .

# lint and apply safe fixes
bunx --bun @biomejs/biome lint --apply .
```

run biome in tandem with the repo's default tooling (`tsc --noEmit`, `eslint`, `prettier`, etc). don't replace the repo's setup — supplement it.

## type checking

always run `tsc --noEmit` before committing. don't rely solely on your editor.

```bash
# check types without emitting
bunx --bun tsc --noEmit
```

## general

- prefer `bunx --bun` for typescript-based tools (they'll run faster)
- use plain `bunx` if `--bun` causes compatibility issues
- run biome checks in addition to repo defaults, not instead of
