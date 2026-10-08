"""Parse every line of every ```openpona fenced block in the repo's Markdown files.

Convention (see docs): one statement per line; text after ' # ' is a comment;
a leading '! ' expects INVALID, a leading '? ' expects AMBIGUOUS, otherwise RESOLVED.
"""
import re
from pathlib import Path

import pytest

import openpona

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_DIRS = {".venv", "venv", ".git", "node_modules", "__pycache__"}
EXCLUDED_PREFIXES = (("research", "parser_probe"),)
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*(.*?)\s*$")


def _skip(path):
    parts = path.relative_to(ROOT).parts
    if any(p in EXCLUDED_DIRS for p in parts):
        return True
    return any(parts[: len(pre)] == pre for pre in EXCLUDED_PREFIXES)


def _blocks(text):
    """Yield (lineno, raw_line) for each line inside an info-string-exactly-'openpona' fence."""
    fence = None  # (marker char, length, is_openpona)
    for no, raw in enumerate(text.splitlines(), 1):
        m = FENCE.match(raw)
        if fence is None:
            if m:
                marker = m.group(2)
                fence = (marker[0], len(marker), m.group(3) == "openpona")
            continue
        if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= fence[1] and not m.group(3):
            fence = None
            continue
        if fence[2]:
            yield no, raw


def _cases():
    out = []
    for path in sorted(ROOT.rglob("*.md")):
        if _skip(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for no, raw in _blocks(path.read_text(encoding="utf-8")):
            line = raw.split(" # ", 1)[0].strip()
            if not line or line.startswith("#"):
                continue
            expect = "RESOLVED"
            if line.startswith("! "):
                expect, line = "INVALID", line[2:].strip()
            elif line.startswith("? "):
                expect, line = "AMBIGUOUS", line[2:].strip()
            out.append(pytest.param(rel, no, line, expect, id=f"{rel}:{no}"))
    return out


CASES = _cases()


def test_openpona_blocks_exist():
    assert CASES, "no ```openpona fenced blocks found in any Markdown file (convention died?)"


@pytest.mark.parametrize("rel,lineno,line,expect", CASES)
def test_doc_line(rel, lineno, line, expect):
    result = openpona.parse(line)
    assert result.status == expect, (
        f"{rel}:{lineno}: expected {expect}, got {result.status} for {line!r}; "
        f"skeletons={result.skeletons} errors={result.errors}"
    )


# --------------------------------------------------------------------------------------
# TP-12: complete JSON / YAML record examples in the documentation are validated against
# the versioned record profiles (schema/profiles, TP-03) and the agent envelope keys (TP-11).
#
# Convention.  A ```json fence is a COMPLETE RECORD EXAMPLE when it parses as a JSON object
# and declares a "profile" (a record) or carries "event_id" + "idempotency_key" (an
# envelope).  Everything else (fragments with "...", "<64 hex>" placeholders, parse-result
# shapes) is a fragment: it must still parse as JSON unless it contains a placeholder.
# A ```yaml fence is a record TEMPLATE: no YAML parser is a dependency, so its top-level
# keys are read by indentation and must all be fields of the BoundStatement profile.
# --------------------------------------------------------------------------------------
import json  # noqa: E402

from openpona import binding as _binding  # noqa: E402
from openpona import record_schemas as _rs  # noqa: E402
from openpona.agent_pipeline import ENVELOPE_KEYS  # noqa: E402

_PLACEHOLDER = re.compile(r"\.\.\.|<[^>\n]+>")


def _fences(text, langs):
    """Yield (first_line_no, lang, body) for fences whose info string is in `langs`."""
    cur = None
    for no, raw in enumerate(text.splitlines(), 1):
        m = FENCE.match(raw)
        if cur is None:
            if m and m.group(3) in langs:
                cur = (no, m.group(3), m.group(2), [])
            elif m:
                cur = (no, None, m.group(2), [])
            continue
        if m and m.group(2)[0] == cur[2][0] and len(m.group(2)) >= len(cur[2]) and not m.group(3):
            if cur[1]:
                yield cur[0], cur[1], "\n".join(cur[3])
            cur = None
        else:
            cur[3].append(raw)


def _doc_examples(langs):
    out = []
    for path in sorted(ROOT.rglob("*.md")):
        if _skip(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for no, lang, body in _fences(path.read_text(encoding="utf-8"), langs):
            out.append(pytest.param(rel, no, body, id=f"{rel}:{no}"))
    return out


JSON_EXAMPLES = _doc_examples({"json"})
YAML_EXAMPLES = _doc_examples({"yaml", "yml"})


def _json_objects(body):
    """One or several JSON objects in a fence (one per top-level brace group)."""
    dec, i, objs = json.JSONDecoder(), 0, []
    while i < len(body):
        if body[i].isspace():
            i += 1
            continue
        obj, end = dec.raw_decode(body, i)
        objs.append(obj)
        i = end
    return objs


# Pre-profile conceptual sketches (canon/05_addressing.md is frozen, docs/for-agents.md and
# examples/addressing.md predate TP-03) use these flat keys.  They are tolerated EXPLICITLY and
# nowhere else; migrating those sketches to the profile shape is PENDING AUTHOR REVIEW.
LEGACY_YAML_KEYS = {"bound_ref", "surface_address", "candidates", "evidence"}


def test_docs_have_json_and_yaml_examples():
    assert JSON_EXAMPLES and YAML_EXAMPLES, "docs lint found no json/yaml fences (convention died?)"


@pytest.mark.parametrize("rel,lineno,body", JSON_EXAMPLES)
def test_doc_json_example(rel, lineno, body):
    if _PLACEHOLDER.search(body):
        return                                   # fragment with a placeholder: not a complete example
    for obj in _json_objects(body):              # must at least be well-formed JSON
        if not isinstance(obj, dict):
            continue
        if "profile" in obj:
            res = _binding.validate_record(obj)
            assert res.valid, f"{rel}:{lineno}: {obj.get('profile')} example invalid: {res.reason} " \
                              f"{[(i.code, i.path) for i in res.issues]}"
        elif "event_id" in obj and "idempotency_key" in obj:
            unknown = sorted(set(obj) - ENVELOPE_KEYS)
            assert not unknown, f"{rel}:{lineno}: envelope example has unknown keys {unknown}"


@pytest.mark.parametrize("rel,lineno,body", YAML_EXAMPLES)
def test_doc_yaml_template_uses_profile_fields(rel, lineno, body):
    allowed = set(_rs.build_schema("BoundStatement")["properties"]) | LEGACY_YAML_KEYS
    keys = [m.group(1) for m in re.finditer(r"^([A-Za-z_][A-Za-z0-9_]*):", body, re.M)]
    assert keys, f"{rel}:{lineno}: yaml fence has no top-level keys"
    unknown = sorted(set(keys) - allowed)
    assert not unknown, f"{rel}:{lineno}: yaml keys not in the BoundStatement profile: {unknown}"


def test_docs_lint_catches_a_bad_record():
    """Known-negative: the validator used above rejects a record with a smuggled key."""
    good = json.loads((ROOT / "examples" / "records" / "valid" /
                       "agent_event_ci_story_1_observed_red.json").read_text(encoding="utf-8"))
    assert _binding.validate_record(good).valid
    bad = dict(good, permission_granted=True)
    assert not _binding.validate_record(bad).valid
    assert set(ENVELOPE_KEYS) and "permission_granted" not in ENVELOPE_KEYS
