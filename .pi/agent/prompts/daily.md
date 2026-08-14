---
description: Give me a concise daily rundown from my assigned Jira work
argument-hint: "[-Nd|-Nw]"
---
Use the `jira` skill and the `stargate-atlassian` MCP server to generate my Jira daily rundown for ${1:--1d}.

Run the three read-only JQL searches documented in the skill: open work, recently updated work, and recently completed work. Inspect individual tickets only when needed to explain a blocker, high-priority item, or meaningful status change. Do not modify Jira.

Format the result as:

# Daily rundown

## Needs attention
Blocked or high-priority work that needs action. Omit this section when empty.

## In progress
A concise list of active work, grouped when several tickets belong to the same initiative.

## Recent movement
Meaningful updates and completions within the requested window.

## Suggested focus
At most three concrete priorities for today. Clearly label these as suggestions.

Link every mentioned ticket.
