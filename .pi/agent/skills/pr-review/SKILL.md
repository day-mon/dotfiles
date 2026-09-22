---
name: pr-review
description: >
  Use whenever reviewing a pull request or replying on one: posting review
  comments, answering reviewer comments, triaging review feedback, or deciding
  what a PR review requires before merge. ALWAYS use this protocol for any PR
  review work, including "review this PR", "review my PR", "review #123",
  "reply to the comments", "address the feedback", "answer the review", or any
  time PR review comments appear on screen. Same label grammar in both
  directions: every comment the assistant POSTS gets a label, and every comment
  the assistant RECEIVES is triaged by its label. Blocking and perf are
  non-negotiable; questions get direct answers. When the request is only to
  find issues in a diff, run deep-review for the analysis and use this skill
  for how the findings are labeled and replied to.
---

# PR Review

One label grammar drives both halves of PR review: what we write on PRs, and
how we respond to what reviewers write on ours.

Grammar: `label(scope): body`

- `scope` = the file, module, or area the comment is about (e.g. `concierge`,
  `db`, `docker`, or a service name). Lowercase, short, omit only when truly
  global.
- Labels: `blocking`, `perf`, `question`, `suggestion`, `nit`, `praise`.

Non-labeled comments from humans that clearly mean one of these still get
triaged under the closest label.

## Label contract

Blocking is the only category not up for discussion. A reviewer who writes
`blocking` has staked the merge on it; the reply must be a fix or evidence
backed by sources, never deflection.

| Label | Reply contract | Why |
|---|---|---|
| `blocking(scope)` | Fix it, or refuse with cited evidence (docs, code, traces). Never silent, never "we can follow up later". Merge stays blocked until resolved. | Reviewer has staked merge on this. |
| `perf(scope)` | Treat as blocking unless a measurement or cited fact shows the win is trivial. If trivial, reply with the evidence. | Perf concerns in this org tend to be real (DB queries, queues, hot paths). |
| `question(scope)` | Answer directly in the reply, no code change. Ask a clarifying question back only when the ask is genuinely ambiguous. | A question is a request for information, not work. |
| `suggestion(scope)` | Weigh it on the merits. Apply if cheap and correct; otherwise reply explaining why not. | Cheap improvements compound; cheap regressions do too. |
| `nit(scope)` | Batch with other nits into one fix commit, or defer explicitly with a reason. No per-nit debate. | Nits are friction; minimize the round trips they cause. |
| `praise(scope)` | One-line acknowledgement. Nothing else. | Padding praise wastes reviewer attention. |

## Writing review comments (posting on someone's PR)

- Prefix every comment with its label: `blocking(api): this drops the WHERE clause and scans the table`, `question(db): is this index actually used by the hot query?`
- One concern per comment. Never stack a `nit` under a `blocking`.
- Inline comments on the exact line via `gh api`; a top-level summary comment for overall verdict.
- Order the chat-window report for the requester: blocking first, then perf, question, suggestion, nit, praise.

## Replying to review comments (someone reviewed my PR)

1. Fetch comments: `gh pr view <N> --comments` for discussion, and
   `gh api repos/{owner}/{repo}/pulls/<N>/reviews` plus
   `gh api repos/{owner}/{repo}/pulls/<N>/comments` for inline threads.
2. Classify each by label (explicit prefix, else infer closest label).
3. Act per the contract table above. Make code changes first where required.
4. Reply per-thread with `gh api repos/{owner}/{repo}/pulls/comments/<comment_id>/replies -f body="..."`.
   One reply per thread; never a single mega-comment that answers everything off-thread.
5. Commit fixes as `type(scope): address <area> review feedback`
   (conventional commits, matching repo style, e.g. `fix(concierge): address routing review feedback`).
6. Post the chat-window summary ordered blocking → perf → question → suggestion → nit, with each thread linked or quoted in one line.

### Pushback is allowed when the reviewer is wrong

If a `blocking` or any other comment is based on a false premise, answer with
cited evidence (vendor docs, the source code itself, a trace) instead of
complying. Compliance with a wrong "blocking" comment is worse than a
respectful refusal: `blocking(zod): try/catch is the canonical pattern — see
zod docs, JSON example` plus the link.

## Reply examples

Reviewer writes `blocking(db): this query has no tenant filter`
→ Fix the query, push the commit, reply: `Fixed in <sha>: added tenant_id predicate and a regression test.`

Reviewer writes `perf(worker): this job holds the queue while awaiting the API`
→ Either fix it, or reply with evidence: `Measured: p95 enqueue latency unaffected (12ms). The await is on the already-multiplexed HTTP client, not the worker loop. Happy to revisit if you have a trace showing otherwise.`

Reviewer writes `question(concierge): should we fall back to Jira when Glean is empty?`
→ `No — an empty Glean result is a valid answer; falling back would double the tool contract for a case the taxonomy already handles via the ticket tool.`

Reviewer writes `nit(docker): image tag formatting`
→ Fold into the batched `chore(docker): address review nits` commit, reply `Done` on the thread.

## Scope rules

- Review-only: never refactor or "improve" unrelated code while answering review feedback.
- If a comment points at pre-existing untouched code, say so on the thread and leave it out of the fix commit.
- Never post, approve, or merge until every `blocking` and non-trivial `perf` thread is resolved or answered with evidence.
