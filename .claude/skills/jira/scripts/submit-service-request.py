#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "atlassian-python-api>=4,<5",
#   "cyclopts>=3.24,<4",
#   "python-dotenv>=1.1,<2",
# ]
# ///

"""Inspect, validate, and submit Jira Service Management portal forms."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Final, Never, TypeAlias, TypeGuard, cast
from urllib.parse import urlparse

from atlassian import ServiceDesk
from cyclopts import App, Parameter
from dotenv import load_dotenv
from requests import HTTPError, Response

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

PORTAL_PATH_PATTERN: Final = re.compile(
    r"^/servicedesk/customer/portal/(?P<service_desk_id>\d+)"
    r"(?:/group/\d+)?/create/(?P<request_type_id>\d+)/?$"
)
DEFAULT_ENV_FILE: Final = Path.cwd() / ".env.local"
DEFAULT_JIRA_SITE: Final = "https://coreweave.atlassian.net"
DEFAULT_JIRA_EMAIL: Final = "dmontague@coreweave.com"
FIELD_KEYS: Final = ("requestTypeFields", "fields")
TEXT_QUESTION_TYPES: Final = frozenset({"pg", "te", "tl", "ts", "tu", "no"})
RICH_TEXT_QUESTION_TYPES: Final = frozenset({"rt"})
SINGLE_CHOICE_QUESTION_TYPES: Final = frozenset({"cd", "cs", "ob"})
MULTI_CHOICE_QUESTION_TYPES: Final = frozenset({"cc", "cl", "cm"})
DATE_QUESTION_TYPES: Final = frozenset({"da", "dt"})
TIME_QUESTION_TYPES: Final = frozenset({"ti"})
SINGLE_USER_QUESTION_TYPES: Final = frozenset({"us"})
MULTI_USER_QUESTION_TYPES: Final = frozenset({"um"})
FORM_ANSWER_KEYS: Final = frozenset({"adf", "choices", "date", "text", "time", "users"})
app: Final = App(
    help="Inspect, validate, and submit a Jira Service Management portal form."
)


@dataclass(frozen=True)
class PortalTarget:
    base_url: str
    service_desk_id: str
    request_type_id: str


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    email: str
    api_key: str


@dataclass(frozen=True)
class FormField:
    field_id: str
    label: str
    description: str
    schema_type: str
    is_required: bool
    valid_values: tuple[JsonObject, ...]


@dataclass(frozen=True)
class FormQuestion:
    question_id: str
    label: str
    description: str
    question_type: str
    is_required: bool
    choices: tuple[JsonObject, ...]


@dataclass(frozen=True)
class PreparedAnswers:
    request_fields: JsonObject
    form_answers: JsonObject


def fail(message: str) -> Never:
    raise SystemExit(f"error: {message}")


def is_json_value(value: object) -> TypeGuard[JsonValue]:
    if value is None or isinstance(value, bool | int | float | str):
        return True
    if isinstance(value, list):
        return all(is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and is_json_value(item) for key, item in value.items()
        )
    return False


def require_object(value: object, *, context: str) -> JsonObject:
    if not isinstance(value, dict) or not is_json_value(value):
        fail(f"{context} must be a JSON object")
    return cast(JsonObject, value)


def optional_object(value: JsonValue) -> JsonObject | None:
    if not isinstance(value, dict):
        return None
    return value


def normalize_name(value: str) -> str:
    return " ".join(value.casefold().split())


def normalize_site(value: str) -> str:
    site = value.strip().rstrip("/")
    if not site.startswith(("https://", "http://")):
        site = f"https://{site}"
    parsed = urlparse(site)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
        fail(f"invalid Jira site: {value}")
    return f"https://{parsed.netloc}"


def parse_portal_url(value: str) -> PortalTarget:
    """Extract the site and request identifiers from a Jira portal URL."""
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        fail("form URL must be an absolute HTTPS URL")
    if match := PORTAL_PATH_PATTERN.fullmatch(parsed.path):
        return PortalTarget(
            base_url=f"https://{parsed.netloc}",
            service_desk_id=match.group("service_desk_id"),
            request_type_id=match.group("request_type_id"),
        )
    fail(
        "form URL must match "
        "https://<site>/servicedesk/customer/portal/<desk>[/group/<group>]/create/<type>"
    )


def build_config(
    target: PortalTarget, *, site: str, email: str, api_key: str | None
) -> JiraConfig:
    """Assemble Jira auth config from CLI/env values already resolved by cyclopts."""
    configured_site = normalize_site(site)
    if configured_site != target.base_url:
        fail(
            f"form site {target.base_url} does not match configured JIRA_SITE {configured_site}"
        )
    if not api_key:
        fail("missing JIRA_API_KEY in the environment or the dotenv file")
    return JiraConfig(
        base_url=configured_site, email=email.strip() or DEFAULT_JIRA_EMAIL, api_key=api_key.strip()
    )


def parse_options(value: object) -> tuple[JsonObject, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        require_object(item, context="form option")
        for item in value
        if isinstance(item, dict)
    )


def parse_fields(payload: object) -> tuple[FormField, ...]:
    data = require_object(payload, context="request type metadata")
    raw_fields: JsonValue = []
    for key in FIELD_KEYS:
        if key in data:
            raw_fields = data[key]
            break
    if not isinstance(raw_fields, list):
        fail("request type metadata did not contain a field list")

    fields: list[FormField] = []
    for raw_field_value in raw_fields:
        raw_field = require_object(
            raw_field_value, context="request type metadata field"
        )
        field_id = raw_field.get("fieldId")
        if not isinstance(field_id, str) or not field_id:
            fail("request type metadata contained a field without fieldId")
        raw_label = raw_field.get("name", raw_field.get("label", field_id))
        label = raw_label if isinstance(raw_label, str) and raw_label else field_id
        raw_description = raw_field.get("description", "")
        jira_schema = optional_object(raw_field.get("jiraSchema"))
        raw_schema_type = jira_schema.get("type") if jira_schema else ""
        fields.append(
            FormField(
                field_id=field_id,
                label=label,
                description=raw_description if isinstance(raw_description, str) else "",
                schema_type=(
                    raw_schema_type if isinstance(raw_schema_type, str) else ""
                ),
                is_required=raw_field.get("required") is True,
                valid_values=parse_options(raw_field.get("validValues")),
            )
        )
    return tuple(fields)


def layout_question_ids(value: JsonValue) -> tuple[str, ...]:
    found: list[str] = []

    def visit(node: JsonValue) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            return
        attrs = optional_object(node.get("attrs"))
        if attrs and attrs.get("extensionKey") == "question":
            parameters = optional_object(attrs.get("parameters"))
            question_id = parameters.get("id") if parameters else None
            if isinstance(question_id, str | int):
                found.append(str(question_id))
        for child in node.values():
            visit(child)

    visit(value)
    return tuple(dict.fromkeys(found))


def parse_questions(payload: object | None) -> tuple[FormQuestion, ...]:
    if payload is None:
        return ()
    data = require_object(payload, context="portal form template")
    design = optional_object(data.get("design"))
    questions = optional_object(design.get("questions")) if design else None
    if questions is None:
        return ()

    layout = design.get("layout") if design else None
    ordered_ids = list(layout_question_ids(layout))
    ordered_ids.extend(
        question_id for question_id in questions if question_id not in ordered_ids
    )

    parsed: list[FormQuestion] = []
    for question_id in ordered_ids:
        raw_question_value = questions.get(question_id)
        if raw_question_value is None:
            continue
        raw_question = require_object(
            raw_question_value, context=f"portal form question {question_id}"
        )
        raw_label = raw_question.get("label", question_id)
        label = raw_label if isinstance(raw_label, str) and raw_label else question_id
        raw_description = raw_question.get("description", "")
        raw_type = raw_question.get("type", "")
        validation = optional_object(raw_question.get("validation"))
        parsed.append(
            FormQuestion(
                question_id=question_id,
                label=label,
                description=raw_description if isinstance(raw_description, str) else "",
                question_type=raw_type if isinstance(raw_type, str) else "",
                is_required=validation is not None and validation.get("rq") is True,
                choices=parse_options(raw_question.get("choices")),
            )
        )
    return tuple(parsed)


def option_label(option: JsonObject) -> str | None:
    for key in ("label", "name", "text"):
        value = option.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def option_value(option: JsonObject) -> JsonValue:
    return option.get("value", option.get("id"))


def map_option(
    value: JsonValue, *, label: str, options: tuple[JsonObject, ...]
) -> JsonValue:
    if not options or not isinstance(value, str):
        return value
    normalized = normalize_name(value)
    for option in options:
        candidate_label = option_label(option)
        candidate = option_value(option)
        if candidate_label and normalize_name(candidate_label) == normalized:
            return candidate
        if isinstance(candidate, str) and normalize_name(candidate) == normalized:
            return candidate
    choices = [
        candidate_label
        for option in options
        if (candidate_label := option_label(option))
    ]
    fail(f"invalid value {value!r} for {label}; choose one of: {', '.join(choices)}")


def option_id_object(mapped: JsonValue, label: str) -> JsonObject:
    if not isinstance(mapped, str):
        fail(f"{label} requires exactly one option value")
    return {"id": mapped}


def map_request_field(value: JsonValue, field: FormField) -> JsonValue:
    if isinstance(value, list):
        mapped: JsonValue = [
            map_option(item, label=field.label, options=field.valid_values)
            for item in value
        ]
    else:
        mapped = map_option(value, label=field.label, options=field.valid_values)
    if field.schema_type == "priority":
        return option_id_object(mapped, field.label)
    if field.schema_type == "option":
        if isinstance(mapped, list):
            return [option_id_object(item, field.label) for item in mapped]
        return option_id_object(mapped, field.label)
    return mapped


def require_text_answer(value: JsonValue, question: FormQuestion) -> str:
    if not isinstance(value, str):
        fail(f"{question.label} requires a text value")
    return value


def require_string_list(value: JsonValue, question: FormQuestion) -> list[JsonValue]:
    raw_values = value if isinstance(value, list) else [value]
    if not all(isinstance(item, str) for item in raw_values):
        fail(f"{question.label} requires a string or list of strings")
    return list(raw_values)


def text_to_adf(value: str) -> JsonObject:
    paragraphs: list[JsonValue] = []
    for paragraph in value.split("\n\n"):
        content: list[JsonValue] = []
        for line_number, line in enumerate(paragraph.splitlines() or [""]):
            if line_number > 0:
                content.append({"type": "hardBreak"})
            if line:
                content.append({"type": "text", "text": line})
        paragraphs.append({"type": "paragraph", "content": content})
    return {"version": 1, "type": "doc", "content": paragraphs}


def map_form_question(value: JsonValue, question: FormQuestion) -> JsonObject:
    if isinstance(value, dict):
        answer = require_object(value, context=f"answer for {question.label}")
        if len(answer) != 1 or not set(answer).issubset(FORM_ANSWER_KEYS):
            fail(
                f"structured answer for {question.label} must contain exactly one of: "
                f"{', '.join(sorted(FORM_ANSWER_KEYS))}"
            )
        return answer

    question_type = question.question_type
    if question_type in TEXT_QUESTION_TYPES:
        return {"text": require_text_answer(value, question)}
    if question_type in RICH_TEXT_QUESTION_TYPES:
        return {"adf": text_to_adf(require_text_answer(value, question))}
    if question_type in DATE_QUESTION_TYPES:
        return {"date": require_text_answer(value, question)}
    if question_type in TIME_QUESTION_TYPES:
        return {"time": require_text_answer(value, question)}
    if question_type in SINGLE_CHOICE_QUESTION_TYPES | MULTI_CHOICE_QUESTION_TYPES:
        values = require_string_list(value, question)
        mapped: list[JsonValue] = [
            map_option(item, label=question.label, options=question.choices)
            for item in values
        ]
        if question_type in SINGLE_CHOICE_QUESTION_TYPES and len(mapped) != 1:
            fail(f"{question.label} accepts exactly one choice")
        return {"choices": mapped}
    if question_type in SINGLE_USER_QUESTION_TYPES | MULTI_USER_QUESTION_TYPES:
        users = require_string_list(value, question)
        if question_type in SINGLE_USER_QUESTION_TYPES and len(users) != 1:
            fail(f"{question.label} accepts exactly one user account ID")
        return {"users": users}
    fail(
        f"unsupported Jira Form question type {question_type!r} for {question.label}; "
        "provide a structured answer object"
    )


def add_alias(
    aliases: dict[str, tuple[str, FormField | FormQuestion]],
    alias: str,
    kind: str,
    target: FormField | FormQuestion,
) -> None:
    normalized = normalize_name(alias)
    existing = aliases.get(normalized)
    if existing and existing != (kind, target):
        fail(f"form has ambiguous field label or ID: {alias}")
    aliases[normalized] = (kind, target)


def build_answers(
    fields: tuple[FormField, ...],
    questions: tuple[FormQuestion, ...],
    answers: JsonObject,
) -> PreparedAnswers:
    aliases: dict[str, tuple[str, FormField | FormQuestion]] = {}
    for field in fields:
        add_alias(aliases, field.field_id, "field", field)
        add_alias(aliases, field.label, "field", field)
    for question in questions:
        add_alias(aliases, question.question_id, "question", question)
        add_alias(aliases, question.label, "question", question)

    request_fields: JsonObject = {}
    form_answers: JsonObject = {}
    unknown: list[str] = []
    for answer_name, answer in answers.items():
        match = aliases.get(normalize_name(answer_name))
        if match is None:
            unknown.append(answer_name)
            continue
        kind, target = match
        if kind == "field" and isinstance(target, FormField):
            if target.field_id in request_fields:
                fail(f"field {target.label} was answered more than once")
            request_fields[target.field_id] = map_request_field(answer, target)
        elif isinstance(target, FormQuestion):
            if target.question_id in form_answers:
                fail(f"question {target.label} was answered more than once")
            form_answers[target.question_id] = map_form_question(answer, target)
    if unknown:
        fail(f"answers contain unknown fields: {', '.join(sorted(unknown))}")

    missing_fields = [
        field.label
        for field in fields
        if field.is_required
        and (
            field.field_id not in request_fields
            or request_fields[field.field_id] in (None, "", [])
        )
    ]
    missing_questions = [
        question.label
        for question in questions
        if question.is_required and question.question_id not in form_answers
    ]
    missing = missing_fields + missing_questions
    if missing:
        fail(f"missing required fields: {', '.join(missing)}")
    return PreparedAnswers(request_fields=request_fields, form_answers=form_answers)


def load_answers(path: Path) -> JsonObject:
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"answers file does not exist: {path}")
    except json.JSONDecodeError as error:
        fail(f"answers file is not valid JSON: {error}")
    return require_object(value, context="answers file")


def option_labels(options: tuple[JsonObject, ...]) -> list[JsonValue]:
    return [label for option in options if (label := option_label(option))]


def answers_template(
    fields: tuple[FormField, ...],
    questions: tuple[FormQuestion, ...],
) -> JsonObject:
    """Build a fill-in answers stub keyed by visible labels, required entries first."""

    def placeholder(
        _label: str,
        _description: str,
        schema_type: str,
        choices: tuple[JsonObject, ...],
    ) -> JsonValue:
        labels = option_labels(choices)
        if labels:
            return f"<choose: {' | '.join(str(lbl) for lbl in labels)}>"
        if schema_type == "date":
            return "YYYY-MM-DD"
        if schema_type == "time":
            return "HH:mm"
        if schema_type == "user":
            return "<Jira account ID>"
        return ""

    entries: list[tuple[bool, str, JsonValue]] = []
    for field in fields:
        entries.append(
            (
                field.is_required,
                field.label,
                placeholder(
                    field.label,
                    field.description,
                    field.schema_type,
                    field.valid_values,
                ),
            )
        )
    for question in questions:
        question_schema = (
            "date"
            if question.question_type in DATE_QUESTION_TYPES
            else "time"
            if question.question_type in TIME_QUESTION_TYPES
            else "user"
            if question.question_type in SINGLE_USER_QUESTION_TYPES
            else ""
        )
        entries.append(
            (
                question.is_required,
                question.label,
                placeholder(
                    question.label,
                    question.description,
                    question_schema,
                    question.choices,
                ),
            )
        )
    return {
        label: value
        for _, label, value in sorted(entries, key=lambda entry: not entry[0])
    }

def answers_json_schema(
    fields: tuple[FormField, ...],
    questions: tuple[FormQuestion, ...],
) -> JsonObject:
    """Emit a JSON Schema describing the answers file for this form."""
    properties: JsonObject = {}
    required: list[JsonValue] = []

    def entry(
        label: str,
        description: str,
        is_multi: bool,
        choices: tuple[JsonObject, ...],
        extra_types: dict[str, JsonValue],
    ) -> JsonObject:
        item_schema: dict[str, JsonValue] = {"type": "string"}
        if labels := option_labels(choices):
            item_schema["enum"] = labels
        item_schema.update(extra_types)
        if description:
            item_schema["description"] = description
        if is_multi:
            return {"type": "array", "items": dict(item_schema)}
        return dict(item_schema)

    for field in fields:
        if field.is_required:
            required.append(field.label)
        multi = field.schema_type.endswith("s")
        extra: dict[str, JsonValue] = {}
        if field.schema_type == "date":
            extra["format"] = "date"
        elif field.schema_type == "number":
            extra["type"] = "number"
        properties[field.label] = entry(
            field.label, field.description, multi, field.valid_values, extra
        )
    for question in questions:
        if question.is_required:
            required.append(question.label)
        extra = {}
        if question.question_type in DATE_QUESTION_TYPES:
            extra["format"] = "date"
        if question.question_type in TIME_QUESTION_TYPES:
            extra["pattern"] = "^\\d{2}:\\d{2}$"
        multi = question.question_type in (
            MULTI_CHOICE_QUESTION_TYPES | MULTI_USER_QUESTION_TYPES
        )
        properties[question.label] = entry(
            question.label, question.description, multi, question.choices, extra
        )

    schema: JsonObject = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Jira portal answers",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }
    return schema


def field_summary(field: FormField) -> JsonObject:
    summary: JsonObject = {
        "fieldId": field.field_id,
        "label": field.label,
        "schemaType": field.schema_type,
        "required": field.is_required,
    }
    if field.description:
        summary["description"] = field.description
    if choices := option_labels(field.valid_values):
        summary["choices"] = choices
    return summary


def question_summary(question: FormQuestion) -> JsonObject:
    summary: JsonObject = {
        "questionId": question.question_id,
        "label": question.label,
        "type": question.question_type,
        "required": question.is_required,
    }
    if question.description:
        summary["description"] = question.description
    if choices := option_labels(question.choices):
        summary["choices"] = choices
    return summary


def fetch_portal_form(client: ServiceDesk, target: PortalTarget) -> JsonObject | None:
    tenant_raw: object = client.get(
        f"{target.base_url}/_edge/tenant_info", absolute=True
    )
    tenant = require_object(tenant_raw, context="Atlassian tenant metadata")
    cloud_id = tenant.get("cloudId")
    if not isinstance(cloud_id, str) or not cloud_id:
        fail("Atlassian tenant metadata did not include cloudId")
    url = (
        f"https://api.atlassian.com/jira/forms/cloud/{cloud_id}/servicedesk/"
        f"{target.service_desk_id}/requesttype/{target.request_type_id}/form"
    )
    try:
        raw_form: object = client.get(url, absolute=True)
    except HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            return None
        raise
    return require_object(raw_form, context="portal form template")


def build_request_payload(
    target: PortalTarget,
    prepared: PreparedAnswers,
    *,
    raise_on_behalf_of: str | None,
) -> JsonObject:
    payload: JsonObject = {
        "isAdfRequest": False,
        "serviceDeskId": target.service_desk_id,
        "requestTypeId": target.request_type_id,
        "requestFieldValues": prepared.request_fields,
    }
    if prepared.form_answers:
        payload["form"] = {"answers": prepared.form_answers}
    if raise_on_behalf_of:
        payload["raiseOnBehalfOf"] = raise_on_behalf_of
    return payload


def request_link(result: JsonObject) -> str | None:
    links = result.get("_links")
    if not isinstance(links, dict):
        return None
    for key in ("web", "agent", "self"):
        value = links.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def sdk_response_json(response: Response, *, context: str) -> JsonObject:
    try:
        raw_value: object = response.json()
    except ValueError:
        fail(
            f"{context} returned a non-JSON response with status {response.status_code}"
        )
    return require_object(raw_value, context=context)


def validate_request(client: ServiceDesk, payload: JsonObject) -> JsonObject | None:
    """Validate without mutation when the Jira tenant exposes that endpoint."""
    raw_response: object = client.post(
        "rest/servicedeskapi/request/validate",
        json=payload,
        headers=client.default_headers,
        advanced_mode=True,
    )
    if not isinstance(raw_response, Response):
        fail("Jira SDK did not return an HTTP response for request validation")
    if raw_response.status_code == 404:
        return None
    if not raw_response.ok:
        error = sdk_response_json(raw_response, context="request validation error")
        print(json.dumps({"validationError": error}, indent=2))
        fail(f"Jira request validation failed with status {raw_response.status_code}")
    return sdk_response_json(raw_response, context="request validation response")


def create_request(client: ServiceDesk, payload: JsonObject) -> JsonObject:
    """Create one request and expose Jira field errors without an SDK traceback."""
    raw_response: object = client.post(
        "rest/servicedeskapi/request",
        json=payload,
        headers=client.default_headers,
        advanced_mode=True,
    )
    if not isinstance(raw_response, Response):
        fail("Jira SDK did not return an HTTP response for request creation")
    if not raw_response.ok:
        error = sdk_response_json(raw_response, context="create request error")
        print(json.dumps({"createError": error}, indent=2))
        fail(f"Jira request creation failed with status {raw_response.status_code}")
    return sdk_response_json(raw_response, context="create request response")


@app.default
def main(
    form_url: str,
    *,
    answers: Path | None = None,
    raise_on_behalf_of: str | None = None,
    env_file: Path = DEFAULT_ENV_FILE,
    apply: bool = False,
    verbose: bool = False,
    schema_: Annotated[bool, Parameter(name="schema")] = False,
    jira_site: Annotated[
        str, Parameter(env_var="JIRA_SITE", show_env_var=True)
    ] = DEFAULT_JIRA_SITE,
    jira_email: Annotated[
        str, Parameter(env_var=["ATLASSIAN_EMAIL", "JIRA_EMAIL"], show_env_var=True)
    ] = DEFAULT_JIRA_EMAIL,
    jira_api_key: Annotated[
        str | None,
        Parameter(
            env_var=["JIRA_API_KEY", "ATLASSIAN_API_TOKEN"],
            show_env_var=True,
        ),
    ] = None,
) -> None:
    """Inspect a portal form, validate answers, and optionally create its request.

    Parameters
    ----------
    form_url
        Jira Service Management customer portal create-request URL.
    answers
        JSON object keyed by a visible field label, question label, or returned ID.
    raise_on_behalf_of
        Optional requester email. Omit to submit as the authenticated account.
    env_file
        Accepted for compatibility; dotenv files are preloaded before parsing
        (defaults to .env.local in the current directory).
    apply
        Create the request after server-side validation. The default is a dry run.
    verbose
        Print the raw form schema instead of the answers template.
    schema_
        Print a JSON Schema describing the answers file for this form.
    jira_site
        Atlassian site base URL. Resolved from JIRA_SITE by default.
    jira_email
        Jira account email. Resolved from ATLASSIAN_EMAIL or JIRA_EMAIL by default.
    jira_api_key
        Jira API key. Resolved from JIRA_API_KEY or ATLASSIAN_API_TOKEN by default.
    """
    target = parse_portal_url(form_url)
    resolved_env_file = env_file.expanduser().resolve()
    config = build_config(
        target, site=jira_site, email=jira_email, api_key=jira_api_key
    )
    client = ServiceDesk(
        url=config.base_url,
        username=config.email,
        password=config.api_key,
        cloud=True,
    )
    try:
        metadata_raw: object = client.get(
            "rest/servicedeskapi/servicedesk/"
            f"{target.service_desk_id}/requesttype/{target.request_type_id}/field",
            headers=client.experimental_headers,
        )
        portal_form = fetch_portal_form(client, target)
        fields = parse_fields(metadata_raw)
        questions = parse_questions(portal_form)

        if answers is None and not schema_:
            if verbose:
                print(
                    json.dumps(
                        {
                            "formUrl": form_url,
                            "serviceDeskId": target.service_desk_id,
                            "requestTypeId": target.request_type_id,
                            "requestFields": [
                                field_summary(field) for field in fields
                            ],
                            "formQuestions": [
                                question_summary(question) for question in questions
                            ],
                        },
                        indent=2,
                    )
                )
            else:
                print(json.dumps(answers_template(fields, questions), indent=2))
            print(
                "inspection only; fill the template, save it, "
                "and re-run with --answers <file.json>"
            )
            return
        if schema_ and answers is None:
            print(json.dumps(answers_json_schema(fields, questions), indent=2))
            return

        prepared = build_answers(
            fields,
            questions,
            load_answers(answers.expanduser().resolve()),
        )
        payload = build_request_payload(
            target,
            prepared,
            raise_on_behalf_of=raise_on_behalf_of,
        )
        print(json.dumps({"request": payload}, indent=2))

        validation = validate_request(client, payload)
        if validation is None:
            print(
                "validation: local checks passed; "
                "Jira validation endpoint unavailable (404)"
            )
        elif validation.get("valid") is not True:
            print(json.dumps({"validation": validation}, indent=2))
            fail("Jira rejected the request during non-mutating validation")
        else:
            print("validation: passed")

        if not apply:
            print("dry run only; pass --apply to create this request")
            return

        result = create_request(client, payload)
        issue_key = result.get("issueKey")
        issue_id = result.get("issueId")
        if not isinstance(issue_key, str) and not isinstance(issue_id, str | int):
            fail("Jira did not return an issue key or issue ID")
        print(
            json.dumps(
                {"created": issue_key or issue_id, "url": request_link(result)},
                indent=2,
            )
        )
    finally:
        client.close()


if __name__ == "__main__":
    # Cyclopts resolves Parameter(env_var=...) during CLI parsing, so any
    # dotenv values must be present in os.environ before the parse happens.
    load_dotenv(DEFAULT_ENV_FILE, override=False)
    app()
