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
    "product-scope.md", "task-contract.md", "workspace-policy.md",
    "browser-workflow.md", "desktop-workflow.md", "hybrid-workflow.md",
    "execution-policy.md",
}
REQUIRED_WORKSPACE_EXAMPLES = {
    "workspace.initial.json", "workspace.running.json",
    "workspace.handoff.json", "workspace.blocked.json",
    "workspace.completed.json",
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


def changelog_version() -> str:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    if not match:
        raise ValueError("CHANGELOG.md has no version heading")
    return match.group(1)


def validate_version_consistency(errors: list[str]) -> None:
    try:
        expected = changelog_version()
    except ValueError as exc:
        errors.append(str(exc))
        return
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^\s*version:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    if not match:
        errors.append("SKILL.md frontmatter has no version field")
        return
    if match.group(1).strip() != expected:
        errors.append(
            f"SKILL.md version {match.group(1).strip()!r} does not match CHANGELOG version {expected!r}"
        )


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
    schema_path = ROOT / "schemas" / "workspace.schema.json"
    if not schema_path.is_file():
        errors.append("Missing workspace schema: schemas/workspace.schema.json")
    evaluation_v2_schema = ROOT / "evaluations" / "v2" / "result.schema.json"
    if not evaluation_v2_schema.is_file():
        errors.append("Missing V2 evaluation schema: evaluations/v2/result.schema.json")
    evaluation_v2_example = ROOT / "evaluations" / "v2" / "example-results.json"
    if not evaluation_v2_example.is_file():
        errors.append("Missing V2 evaluation example: evaluations/v2/example-results.json")
    examples_dir = ROOT / "examples"
    present_examples = {path.name for path in examples_dir.glob("*.json")} if examples_dir.is_dir() else set()
    missing_examples = sorted(REQUIRED_WORKSPACE_EXAMPLES - present_examples)
    if missing_examples:
        errors.append(f"Missing workspace examples: {', '.join(missing_examples)}")
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for relative in sorted(set(re.findall(r"(?:references|scripts|evaluations|schemas|examples)/[A-Za-z0-9_.-]+", text))):
        if not (ROOT / relative).exists():
            errors.append(f"SKILL.md references missing resource: {relative}")


def validate_markdown_links(errors: list[str]) -> None:
    paths = [ROOT / "README.md", ROOT / "README.zh-CN.md", *sorted((ROOT / "docs").glob("*.md"))]
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            local = target.split("#", 1)[0]
            if local and not (path.parent / local).resolve().exists():
                errors.append(f"Broken local link in {path.relative_to(ROOT)}: {target}")


def validate_json(errors: list[str]) -> None:
    paths = [
        ROOT / "evaluations/result.schema.json",
        ROOT / "evaluations/example-results.json",
        ROOT / "evaluations/v2/result.schema.json",
        ROOT / "evaluations/v2/example-results.json",
        ROOT / "schemas/workspace.schema.json",
        *sorted((ROOT / "examples").glob("*.json")),
    ]
    decoded = {}
    for path in paths:
        try:
            decoded[path] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"JSON error in {path.relative_to(ROOT)}: {exc}")
    try:
        schema = decoded[ROOT / "evaluations/result.schema.json"]
        example = decoded[ROOT / "evaluations/example-results.json"]
    except KeyError:
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
    for path, data in decoded.items():
        if path.parent == ROOT / "examples" and data.get("schema_version") != "1.0.0":
            errors.append(f"Workspace example {path.name} must use schema_version 1.0.0")


def validate_python(errors: list[str]) -> None:
    for directory in ("scripts", "tests"):
        for path in sorted((ROOT / directory).glob("*.py")):
            try:
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as exc:
                errors.append(f"Python syntax error in {path.relative_to(ROOT)}: {exc}")


def main() -> int:
    errors: list[str] = []
    validate_version_consistency(errors)
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
