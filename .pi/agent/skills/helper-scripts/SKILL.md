---
name: helper-scripts
description: >
  How to write scripts as an agent — file-based or inline heredocs. Use
  whenever writing a script file (one-off or reusable) or an inline script
  via heredoc (uv run - <<'SCRIPT'). Covers: bash and Python only (never
  Ruby/Perl/Node), uv run with PEP 723 headers, quoted heredoc delimiters,
  no chmod/shebang dependence, and where to put scripts. Triggers on "write
  a script", "run this inline", heredocs, "automate this", "one-off script".
---

# Helper Scripts

Rules for creating scripts as an agent. Follow these every time you write a
script file, whether it is a one-off or something the user will keep.

## Language choice

1. **Bash first.** If the task is a pipeline of existing commands (files,
   processes, curl, jq, git), write bash.
2. **Python when logic gets real.** If the task needs data structures, JSON
   manipulation beyond what jq handles cleanly, error handling, third-party
   libraries, or more than ~40 lines, write Python.
3. **Nothing else.** Do not use Ruby, Perl, PHP, Node one-offs, or any other
   language unless the user explicitly asks.

## Where to put the script

- **One-off / throwaway:** a scratch dir tied to the task, e.g.
  `/private/tmp/<task-name>/script.py`. Tell the user the path.
- **Reusable within a project:** `scripts/` in the project root. If the
  project already has a `bin/` or `tools/` convention, use that instead.
- Never scatter scripts in random directories or the repo root.

## Inline scripts (heredocs)

The same rules apply when the "script" is a heredoc piped to an
interpreter. The language rules do not stop applying just because there
is no file.

**Default form: `uv run - <<'SCRIPT'`.** `uv run -` reads the program
from stdin, so the heredoc is the script — and the PEP 723 header still
works, so third-party deps are fair game inline:

```bash
# Good — default form
uv run - <<'SCRIPT'
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
import json
import yaml
from pathlib import Path

spec = yaml.safe_load(Path("spec.yaml").read_text())
print(json.dumps(spec))
SCRIPT

# Fine for pure-stdlib one-liners
python3 - <<'SCRIPT'
import json
from pathlib import Path
for path in Path.cwd().rglob('*'):
    print(path)
SCRIPT

# Bad — never do this
ruby <<'RUBY'
require 'yaml'
puts YAML.safe_load(File.read('spec.yaml'))
RUBY
```

Rules for inline scripts:

1. **Prefer `uv run - <<'SCRIPT'`** over bare `python3` so the
   interpreter version is pinned and deps resolve automatically. Plain
   `python3 - <<'SCRIPT'` is acceptable only for trivial stdlib-only
   snippets.
2. **Same language rule: bash + Python only.** Do not reach for Ruby,
   Perl, Node, or anything else because it happens to parse YAML nicely
   today. Python's `yaml`/`json`/`tomllib` or `yq`/`jq` cover it.
3. **Always quote the delimiter** (`<<'SCRIPT'`, not `<<SCRIPT`) so the
   shell does not expand `$` or backticks inside your script. Use
   `SCRIPT` as the delimiter name.
4. **Upgrade to a file when**: the snippet is more than ~30 lines, you
   need to run it more than once, or the user might want it again. At
   that point use a real script with `uv run script.py`.

## How to run scripts

**Never `chmod +x`. Never rely on a shebang.** Call the runner directly:

- Python: `uv run script.py` (see below — this is the default for Python)
- Bash: `bash script.sh`

This works everywhere: no executable bit to lose across filesystems, CI, or
copy-paste, and `uv run` handles the Python environment automatically.

## Python: uv single-file scripts (default)

Write Python helpers as [uv single-file scripts] with a PEP 723 header. `uv
run` reads the header, resolves dependencies into an ephemeral environment,
and runs the script — no venv setup, no requirements file, no chmod.

Template:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///

"""One line on what this does.

Usage: uv run do_thing.py <input> [output]
"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("output", nargs="?", default="out.txt")
    args = parser.parse_args()

    # work happens here
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
```

Rules:

- Always include the `# /// script` header with `requires-python`, even with
  zero dependencies. It pins the interpreter and makes the intent obvious.
- Declare third-party deps in `dependencies`, never tell the user to
  `pip install` anything.
- Print progress to stdout so the user sees what happened.
- Run it yourself with `uv run` before handing it over.

[uv single-file scripts]: https://docs.astral.sh/uv/guides/scripts/

## Bash template

```bash
#!/usr/bin/env bash
set -euo pipefail

# What this script does, one line.
# Usage: bash do-thing.sh <input> [output]

input="${1:?usage: bash do-thing.sh <input> [output]}"
output="${2:-out.txt}"

# work happens here
echo "wrote ${output}"
```

Bash rules:

- Always `set -euo pipefail`.
- Quote every variable: `"$var"`, never `$var`.
- Validate args with `${1:?...}` so a missing arg fails with a clear message.
- Use `mktemp -d` for temp files.

## Checklist before handing a script to the user

- [ ] Python has a PEP 723 `# /// script` header; bash has `set -euo pipefail`
- [ ] Usage comment at the top
- [ ] Ran it once yourself (`uv run` / `bash`) and confirmed it works
- [ ] Told the user the exact command to run it — and it is not `./script`
