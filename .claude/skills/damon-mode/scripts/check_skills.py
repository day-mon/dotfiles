# /// script
# requires-python = ">=3.12"
# ///
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Self


@dataclass(frozen=True, slots=True)
class Finding:
    path: Path
    message: str

    def render(self, root: Path) -> str:
        return f"{self.path.relative_to(root)}: {self.message}"


@dataclass(frozen=True, slots=True)
class SkillLint:
    root: Path
    known: frozenset[str]

    MANAGED_PREFIXES: ClassVar = ("principle-", "fastapi-")
    MANAGED_NAMES: ClassVar = frozenset(
        {"codebase-design", "coding-standards", "correct", "reflect", "unslop", "benchmark-checklist", "damon-mode"}
    )
    EXTRA_ROOTS: ClassVar = (Path.home() / ".pi" / "agent" / "skills",)
    HUB: ClassVar = "damon-mode"
    SIGNATURE_ONLY: ClassVar = frozenset({"fastapi-sqlalchemy/references/crud-mixin.md"})
    DOCSTRING_ALLOWED: ClassVar = frozenset({"fastapi-alembic"})
    BANNED_IN_CODE: ClassVar = (
        (re.compile(r"\bcelery\b", re.I), "Celery example; the queue is procrastinate"),
        (re.compile(r"asyncpg"), "asyncpg driver; Postgres uses psycopg 3"),
        (re.compile(r"logging\.getLogger\(__name__\)"), "stdlib logger in app code; use structlog"),
        (re.compile(r"\blog\w*\.\w+\(\s*\"[^\"]*%s"), "%s-formatted log; use an event name and fields"),
    )
    BANNED_IN_ANY_CODE: ClassVar = (
        (re.compile(r"\[tool\.pytest\.ini_options\]"), "INI-compat pytest table; use [tool.pytest]"),
        (re.compile(r"from testcontainers\.postgres import"), "deprecated path; use testcontainers.community.postgres"),
        (re.compile(r"unittest\.TestCase|self\.assert[A-Z]"), "unittest style; use plain pytest functions and assert"),
        (re.compile(r"import \{[^}]*\b(http|HttpResponse)\b[^}]*\} from [\"']msw[\"']"), "MSW 2 import; use msw/http"),
        (re.compile(r"onUnhandledRequest"), "MSW 2 option; use onUnhandledFrame"),
        (re.compile(r"\b(test|describe)\.sequential\b"), "removed in Vitest 5; use { concurrent: false }"),
        (re.compile(r"__async_persistence__"), "not a polyfactory option; bind __async_session__"),
    )
    PYTHON_BLOCK: ClassVar = re.compile(r"```python\n(.*?)```", re.S)
    ANY_BLOCK: ClassVar = re.compile(r"```[a-z]*\n(.*?)```", re.S)
    SKILL_TOKEN: ClassVar = re.compile(r"`((?:principle|fastapi)-[a-z-]+[a-z])(?:/[^`]*)?`")
    BACKTICK_NAME: ClassVar = re.compile(r"`([a-z][a-z0-9-]+)`")
    RELATIVE_LINK: ClassVar = re.compile(r"\]\((\.\./[^)#\s]+)")
    SKILL_PATH: ClassVar = re.compile(r"`([a-z][a-z0-9-]+)/((?:references|scripts)/[^`\s]+)`")
    FRONTMATTER_NAME: ClassVar = re.compile(r"^name:\s*(.+)$", re.M)

    @classmethod
    def create(cls, root: Path) -> Self:
        roots = (root, *root.glob("synced/*"), *cls.EXTRA_ROOTS)
        names = {p.parent.name for base in roots if base.is_dir() for p in base.glob("*/SKILL.md")}
        return cls(root=root, known=frozenset(names))

    def run(self) -> list[Finding]:
        findings = [finding for skill in self._managed() for finding in self._check_skill(skill)]
        return [*findings, *self._check_hub()]

    def _managed(self) -> list[Path]:
        return sorted(
            p.parent
            for p in self.root.glob("*/SKILL.md")
            if p.parent.name in self.MANAGED_NAMES or p.parent.name.startswith(self.MANAGED_PREFIXES)
        )

    def _check_skill(self, skill: Path) -> list[Finding]:
        findings = self._check_frontmatter(skill)
        for doc in sorted(skill.rglob("*.md")):
            text = doc.read_text()
            findings += self._check_references(doc, text)
            findings += self._check_code(skill, doc, text)
        return findings

    def _check_frontmatter(self, skill: Path) -> list[Finding]:
        path = skill / "SKILL.md"
        match = self.FRONTMATTER_NAME.search(path.read_text())
        if match is None:
            return [Finding(path, "missing frontmatter name")]
        if match.group(1).strip() != skill.name:
            return [Finding(path, f"frontmatter name {match.group(1).strip()!r} != directory {skill.name!r}")]
        return []

    def _check_references(self, doc: Path, text: str) -> list[Finding]:
        missing_skills = [
            Finding(doc, f"references unknown skill `{name}`")
            for name in sorted(set(self.SKILL_TOKEN.findall(text)))
            if name not in self.known
        ]
        broken_links = [
            Finding(doc, f"broken link {link}")
            for link in sorted(set(self.RELATIVE_LINK.findall(text)))
            if not (doc.parent / link).resolve().exists()
        ]
        broken_paths = [
            Finding(doc, f"missing file `{name}/{rest}`")
            for name, rest in sorted(set(self.SKILL_PATH.findall(text)))
            if name in self.known and (self.root / name).is_dir() and not (self.root / name / rest).exists()
        ]
        return [*missing_skills, *broken_links, *broken_paths]

    def _check_code(self, skill: Path, doc: Path, text: str) -> list[Finding]:
        findings: list[Finding] = []
        rel = doc.relative_to(self.root).as_posix()
        for idx, block in enumerate(self.ANY_BLOCK.findall(text)):
            findings += [
                Finding(doc, f"code block {idx}: {reason}")
                for pattern, reason in self.BANNED_IN_ANY_CODE
                if pattern.search(block)
            ]
        for idx, block in enumerate(self.PYTHON_BLOCK.findall(text)):
            findings += [
                Finding(doc, f"python block {idx}: {reason}")
                for pattern, reason in self.BANNED_IN_CODE
                if pattern.search(block)
            ]
            if '"""' in block and skill.name not in self.DOCSTRING_ALLOWED:
                findings.append(Finding(doc, f"python block {idx}: docstring in example"))
            if rel in self.SIGNATURE_ONLY:
                continue
            try:
                ast.parse(block)
            except SyntaxError as err:
                findings.append(Finding(doc, f"python block {idx}: {err.msg} (line {err.lineno})"))
        return findings

    def _check_hub(self) -> list[Finding]:
        hub = self.root / self.HUB / "SKILL.md"
        text = hub.read_text()
        named = set(self.BACKTICK_NAME.findall(text))
        unindexed = [
            Finding(hub, f"`{skill.name}` is not indexed in the hub")
            for skill in self._managed()
            if skill.name != self.HUB and skill.name not in named
        ]
        unknown = [
            Finding(hub, f"hub names unknown skill `{name}`")
            for name in sorted(named)
            if name.startswith(self.MANAGED_PREFIXES) and name not in self.known
        ]
        return [*unindexed, *unknown]


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    findings = SkillLint.create(root).run()
    for finding in findings:
        print(finding.render(root))
    print(f"{len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
