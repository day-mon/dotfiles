---
description: Use when drafting or improving Jira tickets. Produces clear tickets with Description, Technical Context, Entrance Criteria, and Acceptance Criteria sections, using the bundled template.jinja2.
argument-hint: [ticket goal or rough notes]
---

# Jira ticket writing

Use this skill when the user asks for a Jira ticket, story, task, bug, epic work item, or acceptance criteria.

## Goal

Write tickets that are specific enough for an engineer to pick up without another meeting.

A good ticket should answer:
- **What are we changing?**
- **Why does it matter?**
- **Where should the implementer look?**
- **What must be true before work starts?**
- **How do we know it is done?**

## Required sections

Use these sections, in this order:

1. `Description`
2. `Technical Context` (optional - include only when there is real technical guidance to give; omit the section entirely otherwise)
3. `Entrance Criteria`
4. `Acceptance Criteria`

Use `template.jinja2` from this skill directory as the output shape.

## Description

Write 1 to 3 short sentences.

Include:
- The user-facing or business problem.
- The intended outcome.
- Any important scope boundary.

Avoid:
- Implementation detail that belongs in Technical Context.
- Vague phrases like “make it better” or “clean this up” without specifics.

## Technical Context

Optional. Include this section only when there is real technical guidance to give. If the ticket has no meaningful technical context, omit the section entirely rather than padding it with filler.

When included, write a few bullets with practical implementation guidance.

Include when known:
- Relevant repos, files, services, components, APIs, feature flags, or dashboards.
- Expected implementation approach.
- Constraints, risks, compatibility concerns, data model notes, or migration notes.
- Testing guidance.

Keep this as guidance, not a full design doc. If a technical decision is uncertain, call it out as an open question instead of pretending it is settled.

## Entrance Criteria

Use this section for prerequisites before the ticket can start.

Include:
- Blocking Jira tickets.
- Required decisions or approvals.
- Required designs, specs, API contracts, migrations, or dependencies.
- Required access, credentials, environments, or test data.

When specific tickets exist, include the key and a link:
- `PROJ-123: Short title - https://company.atlassian.net/browse/PROJ-123`

If none exist, write:
- `None identified.`

Do not invent ticket keys or links. If the user mentions dependencies without ticket IDs, list them as unlinked prerequisites.

## Acceptance Criteria

Write concrete, testable bullets.

Render each criterion as a checkable action item (see Workflow note). The checkbox itself means "must be completed," so no emoji marker is needed for normal criteria. Prefix only the special cases:
- `:x:` for work that is explicitly canceled or out of scope.
- `:question_mark:` for unresolved questions that must be answered before completion.

Each criterion should be independently verifiable.

Good examples:
- `The API returns HTTP 400 with a clear validation error when the request is missing an email.`
- `Unit tests cover successful creation, duplicate input, and missing required fields.`
- `:x: Backfilling historical records is not included in this ticket.`
- `:question_mark: Confirm whether admins should bypass the new validation rule.`

Avoid:
- “Works as expected.”
- “Update tests.” without naming what behavior is tested.
- Combining multiple unrelated outcomes into one bullet.

## Workflow

1. Gather missing context from the user if the ticket would otherwise be misleading.
2. Draft the Jira ticket using `template.jinja2`.
3. Keep language direct and scannable.
4. Do not use em dashes.
5. If you make assumptions, put them in Technical Context or Acceptance Criteria as `:question_mark:` items.
6. When creating/editing via the Atlassian MCP, write the body as ADF (`contentFormat: adf`) so rich nodes render:
   - Hot-link referenced issues and URLs as smart links (`inlineCard` nodes), never paste raw URLs.
   - @mention people with real `mention` nodes (look up the accountId), never plain `@Name` text.
   - Render the `:info:` / `:x:` / `:question_mark:` markers as `emoji` nodes.
   - Render the Acceptance Criteria as a Jira action-item list (`taskList` with `taskItem` children, each needing a unique `localId` and `state` of `TODO`/`DONE`) so each criterion is a checkable action item. Keep the emoji marker at the start of each item.
