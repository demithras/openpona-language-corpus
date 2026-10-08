"""Conformance manifest counts, generated from the cases (never typed by hand).

    python tools/conformance_counts.py            # table per file + TOTAL
    python tools/conformance_counts.py --json     # same, machine readable
    python tools/conformance_counts.py --digests  # expectation digest per record id

Counts are by `expect_status` of every record in conformance/*.jsonl.  Exit code 0
when the files are readable and no id is duplicated, 1 otherwise (CI uses this).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
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
    args = ap.parse_args(argv)
    directory = Path(args.dir)
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
