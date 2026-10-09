"""Conformance manifest counts, generated from the cases (never typed by hand).

    python tools/conformance_counts.py            # table per file + TOTAL
    python tools/conformance_counts.py --json     # same, machine readable
    python tools/conformance_counts.py --digests  # expectation digest per record id
    python tools/conformance_counts.py --check    # README.md + MANIFEST.json counts == jsonl counts
    python tools/conformance_counts.py --write    # regenerate those counts in place (release step)

Counts are by `expect_status` of every record in conformance/*.jsonl.  Exit code 0
when the files are readable and no id is duplicated, 1 otherwise (CI uses this).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "conformance"
STATUSES = ("RESOLVED", "INVALID", "AMBIGUOUS")


def load_records(directory: Path = CONFORMANCE):
    """-> list of (file name, line number, record), files in sorted order."""
    out = []
    for path in sorted(Path(directory).glob("*.jsonl")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                out.append((path.name, n, json.loads(line)))
    return out


def count(directory: Path = CONFORMANCE):
    """-> ({file: Counter(status)}, Counter(total))"""
    per_file = collections.OrderedDict()
    total = collections.Counter()
    for fname, _n, rec in load_records(directory):
        per_file.setdefault(fname, collections.Counter())[rec.get("expect_status", "MISSING")] += 1
        total[rec.get("expect_status", "MISSING")] += 1
    return per_file, total


def duplicate_ids(directory: Path = CONFORMANCE):
    seen = collections.Counter(rec.get("id") for _f, _n, rec in load_records(directory))
    return sorted(i for i, c in seen.items() if c > 1)


def expectation_digest(rec: dict) -> str:
    """sha256 of the part of a record that states what the parser must do."""
    body = {k: rec[k] for k in ("surface", "expect_status", "expect_skeletons", "expect_asts")
            if k in rec}
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


README = ROOT / "README.md"
MANIFEST = ROOT / "MANIFEST.json"
_MARK = re.compile(r"(<!-- conformance-counts -->)(.*?)(<!-- /conformance-counts -->)", re.S)


def summary(total) -> dict:
    """{"total": n, "RESOLVED": a, "INVALID": b, "AMBIGUOUS": c} from a status Counter."""
    out = {"total": sum(total.values())}
    for s in STATUSES:
        out[s] = total[s]
    return out


def readme_phrase(counts: dict) -> str:
    return (f"{counts['total']}-case ({counts['RESOLVED']} RESOLVED, "
            f"{counts['INVALID']} INVALID, {counts['AMBIGUOUS']} AMBIGUOUS)")


def check(readme: Path = README, manifest: Path = MANIFEST, directory: Path = CONFORMANCE):
    """-> list of problem strings (empty = documented counts equal the jsonl-derived counts)."""
    _pf, total = count(directory)
    want = summary(total)
    problems = []
    text = Path(readme).read_text(encoding="utf-8")
    found = _MARK.findall(text)
    if not found:
        problems.append(f"{Path(readme).name}: no <!-- conformance-counts --> marker")
    for _a, body, _b in found:
        if body != readme_phrase(want):
            problems.append(f"{Path(readme).name}: states {body!r}, jsonl says {readme_phrase(want)!r}")
    if re.sub(_MARK, "", text) and re.search(r"\b\d+-case\b", re.sub(_MARK, "", text)):
        problems.append(f"{Path(readme).name}: a hand-typed 'N-case' count outside the marker")
    got = json.loads(Path(manifest).read_text(encoding="utf-8")).get("conformance_counts")
    if got != want:
        problems.append(f"{Path(manifest).name}: conformance_counts is {got!r}, jsonl says {want!r}")
    return problems


def write(readme: Path = README, manifest: Path = MANIFEST, directory: Path = CONFORMANCE):
    _pf, total = count(directory)
    want = summary(total)
    text = Path(readme).read_text(encoding="utf-8")
    new, n = _MARK.subn(lambda m: m.group(1) + readme_phrase(want) + m.group(3), text)
    if n == 0:
        raise SystemExit("README.md has no <!-- conformance-counts --> marker")
    Path(readme).write_text(new, encoding="utf-8")
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    data["conformance_counts"] = want
    Path(manifest).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _table(per_file, total):
    other = sorted(set(total) - set(STATUSES))
    cols = list(STATUSES) + other
    width = max([len(f) for f in per_file] + [len("TOTAL"), len("file")])
    head = f"{'file':<{width}}  " + "  ".join(f"{c:>9}" for c in cols) + f"  {'all':>5}"
    lines = [head, "-" * len(head)]
    for fname, c in per_file.items():
        lines.append(f"{fname:<{width}}  " + "  ".join(f"{c[s]:>9}" for s in cols)
                     + f"  {sum(c.values()):>5}")
    lines.append("-" * len(head))
    lines.append(f"{'TOTAL':<{width}}  " + "  ".join(f"{total[s]:>9}" for s in cols)
                 + f"  {sum(total.values()):>5}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default=str(CONFORMANCE))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--digests", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    directory = Path(args.dir)
    if args.write:
        write(directory=directory)
        return 0
    if args.check:
        problems = check(directory=directory)
        dups = duplicate_ids(directory)
        problems += [f"duplicate conformance ids: {dups}"] if dups else []
        for p in problems:
            print(f"COUNT DRIFT: {p}", file=sys.stderr)
        if not problems:
            print("documented conformance counts match conformance/*.jsonl")
        return 1 if problems else 0
    if args.digests:
        digests = {rec["id"]: expectation_digest(rec) for f, _n, rec in load_records(directory)
                   if f == "ambiguity_v2.jsonl"}
        print(json.dumps(digests, indent=2, sort_keys=True))
        return 0
    per_file, total = count(directory)
    dups = duplicate_ids(directory)
    if args.json:
        print(json.dumps({"files": {f: dict(c) for f, c in per_file.items()},
                          "total": dict(total), "all": sum(total.values()),
                          "duplicate_ids": dups}, indent=2, sort_keys=True))
    else:
        print(_table(per_file, total))
        if dups:
            print(f"DUPLICATE IDS: {dups}", file=sys.stderr)
    return 1 if dups else 0


if __name__ == "__main__":
    raise SystemExit(main())
