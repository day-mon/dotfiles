#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "cyclopts>=3.24,<4",
#   "httpx>=0.28,<1",
#   "python-dotenv>=1.1,<2",
# ]
# ///

"""Safely replace same-named Jira attachments using credentials from .env.local."""

from __future__ import annotations

import mimetypes
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from cyclopts import App
from dotenv import load_dotenv

ISSUE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")
DEFAULT_ENV_FILE = Path.cwd() / ".env.local"
DEFAULT_TIMEOUT_SECONDS = 60.0
app = App(help="Safely replace same-named Jira attachments.")


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    email: str
    api_token: str


@dataclass(frozen=True)
class RemoteAttachment:
    id: str
    filename: str


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def load_config(env_file: Path) -> JiraConfig:
    load_dotenv(env_file, override=False)
    site = (
        os.getenv("JIRA_SITE", "")
        .strip()
        .removeprefix("https://")
        .removeprefix("http://")
        .rstrip("/")
    )
    email = os.getenv("ATLASSIAN_EMAIL", "").strip()
    api_token = os.getenv("ATLASSIAN_API_TOKEN", "").strip()
    missing = [
        name
        for name, value in (
            ("JIRA_SITE", site),
            ("ATLASSIAN_EMAIL", email),
            ("ATLASSIAN_API_TOKEN", api_token),
        )
        if not value
    ]
    if missing:
        fail(f"missing {', '.join(missing)} in {env_file}")
    return JiraConfig(base_url=f"https://{site}", email=email, api_token=api_token)


def validated_files(files: list[Path]) -> list[Path]:
    resolved = [path.expanduser().resolve() for path in files]
    missing = [str(path) for path in resolved if not path.is_file()]
    if missing:
        fail(f"attachment files do not exist: {', '.join(missing)}")
    names = [path.name for path in resolved]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        fail(f"replacement filenames must be unique: {', '.join(duplicates)}")
    return resolved


def parse_remote_attachments(payload: dict[str, Any]) -> list[RemoteAttachment]:
    raw = payload.get("fields", {}).get("attachment", [])
    return [
        RemoteAttachment(id=str(attachment["id"]), filename=str(attachment["filename"]))
        for attachment in raw
        if attachment.get("id") and attachment.get("filename")
    ]


def issue_attachments(client: httpx.Client, issue: str) -> list[RemoteAttachment]:
    response = client.get(
        f"/rest/api/3/issue/{quote(issue, safe='')}", params={"fields": "attachment"}
    )
    response.raise_for_status()
    return parse_remote_attachments(response.json())


def upload_attachment(client: httpx.Client, issue: str, path: Path) -> RemoteAttachment:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as attachment:
        response = client.post(
            f"/rest/api/3/issue/{quote(issue, safe='')}/attachments",
            headers={"X-Atlassian-Token": "no-check"},
            files={"file": (path.name, attachment, content_type)},
        )
    response.raise_for_status()
    uploaded = response.json()
    if not isinstance(uploaded, list) or len(uploaded) != 1:
        raise RuntimeError(f"unexpected Jira upload response for {path.name}")
    record = uploaded[0]
    if record.get("filename") != path.name or not record.get("id"):
        raise RuntimeError(
            f"Jira did not confirm the expected filename for {path.name}"
        )
    return RemoteAttachment(id=str(record["id"]), filename=str(record["filename"]))


def delete_attachment(client: httpx.Client, attachment: RemoteAttachment) -> None:
    response = client.delete(f"/rest/api/3/attachment/{quote(attachment.id, safe='')}")
    response.raise_for_status()


@app.default
def main(
    files: list[Path],
    *,
    issue: str,
    env_file: Path = DEFAULT_ENV_FILE,
    apply: bool = False,
) -> None:
    """Replace Jira attachments matched by filename.

    Parameters
    ----------
    files
        Local replacement files. Jira matches existing attachments by filename.
    issue
        Single Jira work item key.
    env_file
        Dotenv file containing JIRA_SITE, ATLASSIAN_EMAIL, and ATLASSIAN_API_TOKEN.
    apply
        Upload replacements and delete the old same-named attachments.
    """
    issue = issue.strip().upper()
    if not ISSUE_PATTERN.fullmatch(issue):
        fail(f"invalid Jira work item key: {issue}")
    replacements = validated_files(files)
    config = load_config(env_file.expanduser().resolve())

    with httpx.Client(
        base_url=config.base_url,
        auth=(config.email, config.api_token),
        timeout=DEFAULT_TIMEOUT_SECONDS,
        headers={"Accept": "application/json"},
    ) as client:
        existing = issue_attachments(client, issue)
        replace_names = {path.name for path in replacements}
        old = [
            attachment
            for attachment in existing
            if attachment.filename in replace_names
        ]

        print(f"issue: {issue}")
        for path in replacements:
            matches = [
                attachment.id for attachment in old if attachment.filename == path.name
            ]
            print(f"upload: {path} ({path.stat().st_size} bytes)")
            print(
                f"delete after upload: {', '.join(matches) if matches else '(no same-named attachment)'}"
            )

        if not apply:
            print("dry run only; pass --apply to perform this replacement")
            return

        uploaded: list[RemoteAttachment] = []
        for path in replacements:
            attachment = upload_attachment(client, issue, path)
            uploaded.append(attachment)
            print(f"uploaded: {attachment.filename} (id {attachment.id})")

        for attachment in old:
            delete_attachment(client, attachment)
            print(f"deleted old: {attachment.filename} (id {attachment.id})")

        final = issue_attachments(client, issue)
        final_ids = {attachment.id for attachment in final}
        missing_uploads = [
            attachment.id for attachment in uploaded if attachment.id not in final_ids
        ]
        stale_ids = [attachment.id for attachment in old if attachment.id in final_ids]
        if missing_uploads or stale_ids:
            raise RuntimeError(
                f"post-update verification failed; missing uploads={missing_uploads}, stale attachments={stale_ids}"
            )
        print(f"updated {len(uploaded)} attachment(s) on {issue}")


if __name__ == "__main__":
    app()
