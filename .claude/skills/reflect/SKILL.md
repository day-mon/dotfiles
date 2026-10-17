---
name: reflect
description: Review the current session with three independent lenses, surface durable learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect or /reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Skip when the conversation is trivial, or when every skill it used was followed correctly. One-offs are not learnings.

## 1. Locate the transcript

Use the current session's transcript file when the harness stores one (Claude Code: newest `~/.claude/projects/<project>/*.jsonl`; pi: the current session file). Confirm it by matching the opening user prompt. Never read transcripts from other projects. If none matches, write a tight digest of the session instead.

## 2. Run three reviewers

Run the three lenses independently, in parallel when the harness has a subagent or background-delegate tool, otherwise one after another in the main thread. Give each its template verbatim, with the transcript path or digest substituted where marked. Reviewers are read-only.

| Lens | Template |
|---|---|
| Judgment | `references/judgment-reviewer.md` |
| Tooling | `references/tooling-reviewer.md` |
| Divergent | `references/divergent-reviewer.md` |

## 3. Synthesize

Run `references/synthesizer.md` with each reviewer's full output inlined where marked. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint, script, metadata flag, or runtime check would enforce more reliably to Backlog, tagged for `correct`. See `principle-encode-lessons-in-structure`.

## 5. Apply

Present the full Accepted / Rejected / Backlog output and wait for explicit approval before applying any edit. The user picks the subset and may redirect routings.

For each approved row:

- Find the rule's owner in the `damon-mode` hub and edit that file only. Never add a second copy of a rule.
- Trivial edit (a bullet, a tightened sentence, a stale fact): do it directly.
- Substantive edit or new skill: follow the `skill-creator` skill.
- `tune description: <skill path>`: rewrite the description so it triggers on the missed case.
- Run `uv run damon-mode/scripts/check_skills.py` from the skills root before declaring done.

## 6. Summarize

- Edits applied: `<skill path>`, one line each.
- New skills: `<skill path>`, one line each (rare).
- Backlog for `correct`: one line each.
- Dropped: one line per rejected finding with the reason.
