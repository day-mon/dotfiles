# Atlassian Document Format (ADF) reference

Use this reference when constructing Jira issue descriptions or comments as ADF JSON.

## Canonical sources

- Document structure: https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/
- JSON schema: http://go.atlassian.com/adf-json-schema
- Node details: `https://developer.atlassian.com/cloud/jira/platform/apis/document/nodes/<node>/`
- Marks: `https://developer.atlassian.com/cloud/jira/platform/apis/document/marks/<mark>/`

The JSON schema can contain nodes or marks that a particular Jira field does not support. Prefer the Jira document-format pages for product support, and validate the final payload against the target API.

## Core structure

ADF is ordered JSON composed of nested nodes:

- Every document has one root `doc` node.
- The root requires `version: 1`, `type: "doc"`, and a `content` array.
- Block nodes define structure, such as `heading`, `paragraph`, `bulletList`, and `taskList`.
- Inline nodes carry content, such as `text`, `emoji`, `mention`, and `inlineCard`.
- Marks format compatible nodes, usually `text`; examples include `strong`, `em`, `code`, and `link`.
- `attrs` stores node- or mark-specific attributes.
- Preserve display order in every `content` array.

Minimal document:

```json
{
  "version": 1,
  "type": "doc",
  "content": []
}
```

## Jira ticket mapping

Build the required ticket sections with these nodes:

| Ticket content | ADF shape |
|---|---|
| Section title | `heading` with `attrs.level: 2` |
| Body copy | `paragraph` containing inline nodes |
| Technical Context / Entrance Criteria | `bulletList` → `listItem` → `paragraph` |
| Acceptance Criteria | `taskList` → `taskItem` |
| Jira issue or URL | `inlineCard` with `attrs.url` |
| Person | `mention` with `attrs.id` set to a real Atlassian account ID |
| Special marker | `emoji` with `attrs.shortName` |

Do not send Markdown syntax inside text nodes and expect Jira to convert it. Encode rich content as ADF nodes and marks.

## Common node recipes

### Heading and paragraph

```json
[
  {
    "type": "heading",
    "attrs": { "level": 2 },
    "content": [{ "type": "text", "text": "Description" }]
  },
  {
    "type": "paragraph",
    "content": [{ "type": "text", "text": "Explain the intended outcome." }]
  }
]
```

Heading levels are `1` through `6`. A paragraph requires `type`; its `content` array is optional when empty.

### Bullet list

```json
{
  "type": "bulletList",
  "content": [
    {
      "type": "listItem",
      "content": [
        {
          "type": "paragraph",
          "content": [{ "type": "text", "text": "None identified." }]
        }
      ]
    }
  ]
}
```

Do not place inline `text` directly under `bulletList` or `listItem`; wrap it in a `paragraph`.

### Acceptance Criteria task list

```json
{
  "type": "taskList",
  "attrs": { "localId": "0e7908f1-98c0-4a9f-8f40-c3a7ef4bcdf6" },
  "content": [
    {
      "type": "taskItem",
      "attrs": {
        "localId": "460d8a7c-9807-4ec7-a526-fcc7289b1393",
        "state": "TODO"
      },
      "content": [
        {
          "type": "text",
          "text": "The API rejects a missing email with HTTP 400."
        }
      ]
    }
  ]
}
```

Rules:

- `taskList` requires `attrs.localId` and at least one child.
- `taskItem` requires a unique `attrs.localId` and `state` of `TODO` or `DONE`.
- `taskItem.content` contains inline nodes directly; do not wrap them in a paragraph.
- Generate fresh UUID-style local IDs within each document.

### Smart link

```json
{
  "type": "inlineCard",
  "attrs": { "url": "https://example.atlassian.net/browse/PROJ-123" }
}
```

An `inlineCard` is an inline node. Put it in a paragraph or task item alongside any surrounding text. Do not add `content` or marks to it.

### Mention

```json
{
  "type": "mention",
  "attrs": {
    "id": "ATLASSIAN_ACCOUNT_ID",
    "text": "@Display Name"
  }
}
```

`attrs.id` is required. Resolve the real account ID before constructing the node; never invent one. `attrs.text` is optional display text.

### Emoji marker

```json
{
  "type": "emoji",
  "attrs": { "shortName": ":question_mark:" }
}
```

`attrs.shortName` is required. Use an `emoji` node rather than literal `:question_mark:` or `:x:` text when writing rich ADF.

A marked task item starts with the emoji and a separating text node:

```json
{
  "type": "taskItem",
  "attrs": {
    "localId": "a6a020bb-e9d0-44d3-9d8a-69e8bf3f873e",
    "state": "TODO"
  },
  "content": [
    { "type": "emoji", "attrs": { "shortName": ":question_mark:" } },
    { "type": "text", "text": " Confirm whether admins bypass validation." }
  ]
}
```

### Text marks

```json
{
  "type": "text",
  "text": "important",
  "marks": [{ "type": "strong" }]
}
```

For a normal inline hyperlink rather than a smart card:

```json
{
  "type": "text",
  "text": "Atlassian documentation",
  "marks": [
    {
      "type": "link",
      "attrs": { "href": "https://developer.atlassian.com/" }
    }
  ]
}
```

For this skill, Jira issue references and standalone URLs should use `inlineCard`; reserve the `link` mark for intentionally linked prose.

## Validation checklist

Before sending ADF to Jira:

- Root is exactly `version: 1`, `type: "doc"`, with ordered `content`.
- Every node is nested under a parent that accepts its type.
- Required `attrs` are present.
- Text nodes contain non-empty strings.
- Account IDs and URLs are real; none were invented.
- Every task list and task item has a unique `localId`.
- Every task item state is `TODO` or `DONE`.
- No Markdown-only syntax is being used as a substitute for ADF.
- The API request declares ADF using the client-specific option, such as `contentFormat: adf` when supported.
