---
name: git-worktrees
description: Activate whenever dealing with git worktrees — creating, listing, moving, or cleaning them up. All worktrees must live in ~/.projects/.worktrees.
---

# Git worktrees

## Location rule

Every worktree goes in `~/.projects/.worktrees/<name>` — nowhere else.

- Name = short task slug (e.g. `ask-hr-sdk-timeout`).
- Do not create worktrees inside the repo, in `/tmp`, or in ad-hoc dirs.
- If a worktree exists elsewhere, flag it and offer to move it.

## Creating

```bash
git -C <repo> worktree add ~/.projects/.worktrees/<name> -b <branch> <base>
```

- Default base: `origin/main` (run `git fetch origin main` first).
- One branch per worktree; never check out a branch already in use.

## Tracking

Keep worktrees discoverable:

```bash
git worktree list
```

Include the worktree path in PR descriptions and session notes so it can be found later.

## Cleanup

When a branch is merged or abandoned:

```bash
git -C <repo> worktree remove ~/.projects/.worktrees/<name>
git branch -d <branch>   # only after merge is confirmed
```

Never `git worktree remove` a worktree with uncommitted changes without explicit confirmation.
