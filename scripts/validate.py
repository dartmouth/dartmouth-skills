#!/usr/bin/env python3
"""Validate skills (Agent Skills spec) and OKF v0.2 frontmatter. Requires PyYAML."""
import datetime as dt
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESERVED = {"index.md", "log.md"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
errors, warnings = [], []


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, text
    head, _, body = text[4:].partition("\n---\n")
    return yaml.safe_load(head) or {}, body


for md in sorted(ROOT.rglob("*.md")):
    if any(p.startswith(".") for p in md.relative_to(ROOT).parts):
        continue
    rel = md.relative_to(ROOT)
    fm, body = frontmatter(md)

    if md.name in RESERVED:
        continue  # index.md / log.md: no frontmatter required (OKF §8–9)

    if fm is None:
        errors.append(f"{rel}: missing YAML frontmatter")
        continue
    if not fm.get("type"):
        errors.append(f"{rel}: OKF requires non-empty 'type'")

    if md.name == "SKILL.md":
        name, desc = fm.get("name", ""), fm.get("description", "")
        if name != md.parent.name:
            errors.append(f"{rel}: name '{name}' must match directory '{md.parent.name}'")
        if not NAME_RE.match(name or "") or len(name) > 64:
            errors.append(f"{rel}: invalid skill name '{name}'")
        if not desc or len(desc) > 1024:
            errors.append(f"{rel}: description missing or > 1024 chars")
        lines = body.count("\n")
        if lines > 500:
            warnings.append(f"{rel}: body is {lines} lines; move detail to references/")

    gen = fm.get("generated")
    if gen is not None and not (isinstance(gen, dict) and gen.get("by")):
        errors.append(f"{rel}: generated.by is required when generated is present")

    ver = fm.get("verified")
    ver = [ver] if isinstance(ver, dict) else (ver or [])
    if fm.get("status") == "stable" and not any(str(v.get("by", "")).startswith("human:") for v in ver):
        warnings.append(f"{rel}: status stable but no human: verification")

    stale = fm.get("stale_after")
    if isinstance(stale, dt.datetime) and stale <= dt.datetime.now(dt.timezone.utc):
        warnings.append(f"{rel}: stale since {stale.isoformat()} — re-check sources")

    ids = set()
    for i, s in enumerate(fm.get("sources") or []):
        if not s.get("resource"):
            errors.append(f"{rel}: sources[{i}] missing resource")
        if s.get("id"):
            ids.add(s["id"])
    prose = re.sub(r"```.*?```|`[^`\n]*`", "", body, flags=re.S)  # ignore code
    for ref in set(re.findall(r"\[\^([\w-]+)\]", prose)):
        if ref not in ids:
            errors.append(f"{rel}: footnote [^{ref}] has no matching sources[].id")

for js in (ROOT / ".claude-plugin").glob("*.json"):
    try:
        json.loads(js.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"{js.relative_to(ROOT)}: invalid JSON ({e})")

for w in warnings:
    print(f"WARN  {w}")
for e in errors:
    print(f"ERROR {e}")
print(f"{'FAIL' if errors else 'OK'}: {len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
