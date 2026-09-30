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
