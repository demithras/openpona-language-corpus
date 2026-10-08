"""CLI: python -m openpona parse|conformance ..."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .parser import parse


def _cmd_parse(args) -> int:
    res = parse(args.sentence)
    if args.json:
        # API 1.0.0: exactly {api_version, status, alternatives}; diagnostics go to stderr
        print(json.dumps(res.to_json(), ensure_ascii=False, indent=2, sort_keys=True))
        for e in res.errors:
            print(f"error: {e}", file=sys.stderr)
    else:
        print(res.status)
        for s in res.skeletons:
            print(s)
        for e in res.errors:
            print(f"error: {e}", file=sys.stderr)
    # 0 RESOLVED/AMBIGUOUS, 1 INVALID (syntax verdict), 3 RESOURCE_EXHAUSTED (no verdict)
    return {"INVALID": 1, "RESOURCE_EXHAUSTED": 3}.get(res.status, 0)


def load_cases(directory: Path) -> list[dict]:
    cases = []
    for path in sorted(directory.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                cases.append(json.loads(line))
    return cases


def run_case(case: dict):
    res = parse(case["surface"])
    exp_status = case["expect_status"]
    exp_skel = sorted(set(case.get("expect_skeletons", [])))
    if exp_status == "INVALID":
        ok = res.status == "INVALID" and res.skeletons == []
    else:
        ok = res.status == exp_status and sorted(set(res.skeletons)) == exp_skel
    return ok, res, exp_status, exp_skel


def _cmd_conformance(args) -> int:
    directory = Path(args.dir)
    if not directory.is_dir():
        alt = Path(__file__).resolve().parent.parent / args.dir
        directory = alt if alt.is_dir() else directory
    cases = load_cases(directory)
    passed = failed = 0
    for case in cases:
        ok, res, exp_status, exp_skel = run_case(case)
        if ok:
            passed += 1
            print(f"PASS {case['id']}")
        else:
            failed += 1
            print(f"FAIL {case['id']}: {case['surface']!r} expected {exp_status} {exp_skel} "
                  f"got {res.status} {res.skeletons}")
    print(f"{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="openpona")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("sentence")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=_cmd_parse)
    c = sub.add_parser("conformance")
    c.add_argument("--dir", default="conformance")
    c.set_defaults(fn=_cmd_conformance)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
