---
name: jira
description: Manage CoreWeave Jira through the authenticated Stargate Atlassian MCP, and draft clear Jira tickets. Use for viewing, searching, creating, editing, assigning, transitioning, commenting on, linking, worklogging, or summarizing Jira issues; daily Jira rundowns; and writing stories, tasks, bugs, epics, or acceptance criteria. Use the small local fallback only for board/sprint administration or attachment replacement, which the MCP does not expose.
argument-hint: [ticket goal, issue key, JQL, or rough notes]
---

# Jira through Stargate

Use the `mcp` gateway with `server: "stargate-atlassian"` for Jira work. Do not use `acli` for normal issue operations.

CoreWeave defaults:

- Site / `cloudId`: `https://coreweave.atlassian.net`
- Issue URL: `https://coreweave.atlassian.net/browse/<KEY>`
- MCP server: `stargate-atlassian`

## Safety

- Run read-only searches and views directly.
- Before a mutation, state the exact issue keys and intended change.
- If the user explicitly requested that exact single-issue change, proceed.
- Ask for confirmation before bulk changes, deletion, archival, attachment deletion/replacement, or a JQL-based mutation.
- Never invent issue keys, project keys, account IDs, field IDs, transition IDs, sprint IDs, or links.
- After a write, verify the affected issue with `getJiraIssue` and report its key and link.

## MCP workflow

1. Discover a tool with `mcp` search when needed.
2. Inspect its schema with `mcp` describe before unfamiliar or write operations.
3. Call it through `mcp` with `server: "stargate-atlassian"`; `args` must be a JSON string.
4. Prefer `responseContentFormat: "markdown"` for reads and `contentFormat: "adf"` for rich writes.

Common Jira tools:

| Goal | Tool |
|---|---|
| Read an issue, including comments or custom fields | `getJiraIssue` |
| Search issues | `searchJiraIssuesUsingJql` |
| Create an issue | `createJiraIssue` |
| Edit fields, assign, set parent/sprint/labels/priority | `editJiraIssue` |
| Find users and account IDs | `lookupJiraAccountId` |
| List projects | `getVisibleJiraProjects` |
| Inspect issue types and fields | `getJiraProjectIssueTypesMetadata`, `getJiraIssueTypeMetaWithFields` |
| Read/add/update comments | `getJiraIssue` with `comment`, `addCommentToJiraIssue` |
| Read/apply transitions | `getTransitionsForJiraIssue`, `transitionJiraIssue` |
| Read/create issue links | `getIssueLinkTypes`, `createIssueLink`, `getJiraIssueRemoteIssueLinks` |
| Add/update worklogs | `addWorklogToJiraIssue` |

### Read an issue

Call `getJiraIssue` with the site URL as `cloudId`, the issue key, and only the fields needed. Include `comment` to retrieve comments. Use `fields: ["*all"]` only when custom-field discovery is necessary because it produces a large response.

### Search with JQL

Use `searchJiraIssuesUsingJql` with targeted fields and `maxResults <= 100`. Follow `nextPageToken` when complete pagination matters. Keep read-only daily/report searches separate rather than building one oversized query.

### Create or edit

- Resolve the project, issue type, user account ID, transition ID, parent, story-points field ID, sprint field ID, and other custom-field IDs before writing.
- Before creating an implementation ticket owned by the user's team, require both a story-point estimate and a destination: a named sprint or the backlog. If either is missing, ask the user one concise question that requests both missing choices. Do not create the ticket until they answer.
- External feature requests and intake submissions owned and triaged by another team are exempt from the story-point and sprint requirement. Leave story points, sprint, and assignee unset unless the user or the destination intake contract explicitly provides them, so the owning project's automation and triage process can route the request.
- Use whole-number story-point estimates from `1` through `8`. Each point represents half a working day: `1` = 0.5 day, `2` = 1 day, `3` = 1.5 days, through `8` = 4 days. If the work appears larger than `8`, recommend splitting it instead of assigning a larger estimate.
- Always set story points during ticket creation. If the selected issue type does not expose a story-points field, stop and explain the field/configuration problem rather than silently creating an unestimated ticket.
- For a named sprint, resolve the real sprint ID before writing and set it during creation. For the backlog, leave the sprint field unset; do not pass `null` unless clearing an existing sprint was explicitly requested.
- `createJiraIssue.additional_fields` is the only place to set priority, labels, components, sprint/custom fields, and similar fields during creation.
- `editJiraIssue.fields` can set standard or `customfield_*` fields, including assignee, parent, sprint, labels, priority, and story points.
- Pass an explicit `null` only when the user intends to clear a field.
- Use `lookupJiraAccountId`; never guess an assignee ID.

### Transition

Call `getTransitionsForJiraIssue`, select the transition whose target status matches the request, then call `transitionJiraIssue` with that transition ID. Do not guess IDs from another project or workflow.

## Daily rundown

For `${window}` style requests such as `-1d` or `-2w`, run these read-only JQL searches through `searchJiraIssuesUsingJql`:

1. Open work:
   `assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated DESC`
2. Recently updated:
   `assignee = currentUser() AND updated >= startOfDay(<window>) ORDER BY updated DESC`
3. Recently completed:
   `assignee = currentUser() AND statusCategory = Done AND statusCategoryChangedDate >= startOfDay(<window>) ORDER BY updated DESC`

Request `summary`, `status`, `priority`, `issuetype`, `assignee`, `parent`, and `updated`. Inspect individual issues only when needed to explain a blocker, high-priority item, or meaningful status change. Do not modify Jira during a rundown.

Format:

- `# Daily rundown`
- `## Needs attention` for blocked/high-priority items; omit when empty
- `## In progress`, grouped by initiative when useful
- `## Recent movement`
- `## Suggested focus`, at most three clearly labeled suggestions

Link every mentioned issue.

# Ticket writing

Use this section when drafting, creating, or improving Jira tickets.

## Required sections

For general tickets, use these sections in order:

1. `Description`
2. `Technical Context` (only when real technical guidance exists)
3. `Entrance Criteria`
4. `Acceptance Criteria`

Use `template.jinja2` from this skill directory as the general output shape.

### Data Infrastructure & Analytics request intake

Use `dia-intake-template.jinja2` when the user asks for a Data Infrastructure & Analytics intake, a BODE intake, or references `/dia-request-intake`. This intake-specific shape replaces the general section order above and mirrors the Canvas app in `apps/it-engineering/dia-request-intake`.

- Use `request_title` as the Jira summary.
- Required inputs are first name, last name, work email, team or department, request title, description/business context, success criteria, target date, and intended consumers.
- Before creating the ticket, ask one compact question for any missing required inputs. Do not block on unanswered optional inputs.
- Optional inputs are manager or sponsor, related Jira tickets, request type, data sources, number of users, data sensitivity, dependencies or blockers, additional notes, and attachments.
- Request Type values are `New dashboard / report`, `New data pipeline / dataset`, `Change to existing pipeline or report`, `Data access / permissions`, `Ad-hoc analysis`, and `Other`. Accept more than one.
- Data Sensitivity values are `PII`, `Standard`, `MNPI`, `SOX`, `Not Applicable`, and `Other (Please Specify)`.
- Require `data_sensitivity_other` only when Data Sensitivity is `Other (Please Specify)`.
- Convert the requester's Success Criteria / Acceptance Criteria text into independently verifiable ADF task items without inventing scope.
- Resolve real Jira issue references and people before using inline cards or mentions. Do not convert unverified free text into links or mentions.
- Omit unanswered optional values where the template allows it; use `None identified.` only for dependencies or blockers and `None provided.` only for additional notes.

The Canvas app currently routes submissions to project `BODE` as a `Story`, with priority `Medium` and parent `BODE-6895`. Treat these as app-specific routing defaults, not universal Jira defaults. This is an external intake: do not require story points or a sprint, and leave the assignee unset for project automation unless the user explicitly requests an assignee. Follow the remaining metadata-discovery and creation safety rules before writing to Jira.

### Description

Write 1 to 3 short sentences covering the user or business problem, intended outcome, and important scope boundary. Keep implementation details in Technical Context.

### Technical Context

Include practical bullets when known: repos, files, services, APIs, flags, dashboards, implementation constraints, risks, compatibility concerns, migration notes, or testing guidance. State uncertain decisions as open questions.

### Entrance Criteria

List blocking tickets, decisions, approvals, designs, contracts, credentials, environments, or test data. Link real tickets as `<KEY>: <title> - https://coreweave.atlassian.net/browse/<KEY>`. If none exist, write `None identified.`

### Acceptance Criteria

Write independently verifiable outcomes. Use checkable ADF action items. Prefix only special cases:

- `:x:` for explicitly canceled or out-of-scope work
- `:question_mark:` for unresolved questions required before completion

Avoid vague criteria such as “works as expected” or “update tests.”

## Completing a story

Before transitioning a story to Done:

1. Verify every Acceptance Criteria item against the delivered work.
2. Mark every satisfied Acceptance Criteria task item as checked in the ticket description. Do not check an item that was not completed; instead, leave it unchecked and explain the gap or move it out of scope explicitly.
3. Add a completion update describing what was done, how it was implemented, and any relevant links, such as pull requests, commits, documentation, dashboards, test results, or follow-up tickets. Use only verified links.
4. Re-read the issue after the edits and confirm that all Acceptance Criteria boxes are checked before transitioning it to Done. If any box remains unchecked, stop and ask how the remaining scope should be handled.

Write the completion update as a concise ADF comment with headings or bold labels for `What was done`, `How it was done`, and `Relevant links`.

## ADF requirement

**Always create or edit ticket descriptions and rich comments in ADF.** Pass `contentFormat: "adf"` and provide an ADF document, not Markdown pretending to be rich text.

Before constructing or debugging ADF, read `references/adf.md`. Required conventions:

- section headings: `heading` nodes
- prose: `paragraph` nodes
- context/prerequisites: `bulletList` nodes
- Acceptance Criteria: `taskList` with `taskItem` children and fresh unique `localId` values
- Jira links and standalone URLs: `inlineCard` nodes
- people: real `mention` nodes after resolving account IDs
- special markers: `emoji` nodes

Do not use em dashes.

# Fallbacks not available through MCP

## Board and sprint administration

The Atlassian MCP can set a known sprint custom field, but it cannot list or administer boards/sprints. Use read-only `acli jira board` commands only when a board or active sprint ID must be discovered. Use `acli jira sprint` for explicit sprint administration requests.

Examples:

```bash
acli jira board search --project IISA --json
acli jira board list-sprints --id <board-id> --state active --json
```

Apply the discovered sprint to an issue through `editJiraIssue`, not through `acli`, unless the MCP cannot represent the required operation.

## Replace attachments

The MCP does not expose Jira attachment upload/delete. Use the bundled dry-run-first helper:

```bash
uv run ~/.claude/skills/jira/scripts/replace-attachments.py \
  --issue IISA-123 path/to/report.xlsx

uv run ~/.claude/skills/jira/scripts/replace-attachments.py \
  --issue IISA-123 --apply path/to/report.xlsx
```

The helper loads `JIRA_SITE`, `ATLASSIAN_EMAIL`, and `ATLASSIAN_API_TOKEN` from `.env.local`, uploads all replacements first, then deletes old same-named attachment IDs. Before `--apply`, report the exact issue, filenames, and attachment IDs from the dry run and obtain explicit confirmation.

## Remaining gaps

The MCP does not provide issue deletion, attachment management, watcher management, worklog deletion, or full board/sprint administration. Explain the gap instead of inventing a tool or undocumented argument.
