#!/usr/bin/env python3
"""Validate the portable skill and repository without network access."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAX_SKILL_LINES = 120
REQUIRED_REFERENCES = {
    "setup.md", "routing.md", "contract.md", "recovery.md",
    "platforms.md", "environments.md", "scenarios.md", "testing.md",
}


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields, text[end + 5:]


def validate_frontmatter(errors: list[str]) -> None:
    path = ROOT / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    try:
        fields, body = frontmatter(text)
    except ValueError as exc:
        errors.append(str(exc))
        return
    name = fields.get("name", "")
    description = fields.get("description", "")
    compatibility = fields.get("compatibility", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append("Invalid Agent Skills name")
    if name != ROOT.name:
        errors.append(f"Skill name {name!r} does not match directory {ROOT.name!r}")
    if not (1 <= len(description) <= 1024):
        errors.append(f"description length must be 1..1024, got {len(description)}")
    if compatibility and len(compatibility) > 500:
        errors.append("compatibility exceeds 500 characters")
    if fields.get("license") and not (ROOT / "LICENSE").is_file():
        errors.append("Frontmatter declares a license but LICENSE is missing")
    if not body.strip():
        errors.append("SKILL.md body is empty")
    lines = len(text.splitlines())
    if lines > MAX_SKILL_LINES:
        errors.append(f"SKILL.md has {lines} lines; project limit is {MAX_SKILL_LINES}")


def validate_resources(errors: list[str]) -> None:
    reference_dir = ROOT / "references"
    present = {path.name for path in reference_dir.glob("*.md")}
    missing = sorted(REQUIRED_REFERENCES - present)
    if missing:
        errors.append(f"Missing references: {', '.join(missing)}")
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for relative in sorted(set(re.findall(r"(?:references|scripts|evaluations)/[A-Za-z0-9_.-]+", text))):
        if not (ROOT / relative).exists():
            errors.append(f"SKILL.md references missing resource: {relative}")


def validate_markdown_links(errors: list[str]) -> None:
    for path in [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            local = target.split("#", 1)[0]
            if local and not (path.parent / local).resolve().exists():
                errors.append(f"Broken local link in {path.relative_to(ROOT)}: {target}")


def validate_json(errors: list[str]) -> None:
    try:
        schema = json.loads((ROOT / "evaluations/result.schema.json").read_text(encoding="utf-8"))
        example = json.loads((ROOT / "evaluations/example-results.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Evaluation JSON error: {exc}")
        return
    required = schema["$defs"]["run"]["required"]
    properties: dict[str, Any] = schema["$defs"]["run"]["properties"]
    for index, run in enumerate(example.get("runs", [])):
        missing = sorted(set(required) - set(run))
        if missing:
            errors.append(f"Example run {index} missing fields: {', '.join(missing)}")
        extra = sorted(set(run) - set(properties))
        if extra:
            errors.append(f"Example run {index} has extra fields: {', '.join(extra)}")
        if run.get("synthetic") is not True:
            errors.append("All bundled example runs must be explicitly synthetic")
        if run.get("agent_claimed_success") is True and run.get("task_success") is False:
            if run.get("evidence_level") == "L3":
                errors.append("Synthetic false-success example cannot claim independent L3 success")
    if not example.get("runs"):
        errors.append("Evaluation example contains no runs")


def validate_python(errors: list[str]) -> None:
    for directory in ("scripts", "tests"):
        for path in sorted((ROOT / directory).glob("*.py")):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                errors.append(f"Python syntax error in {path.relative_to(ROOT)}: {exc}")


def main() -> int:
    errors: list[str] = []
    validate_frontmatter(errors)
    validate_resources(errors)
    validate_markdown_links(errors)
    validate_json(errors)
    validate_python(errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    skill_lines = len((ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines())
    print(f"OK: skill metadata, {skill_lines} core lines, resources, local links, JSON, and Python syntax")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
