#!/usr/bin/env python3
"""META-fold benchmark: fixture generator + per-case timer (TP-01).

Families (n = number of duplicated units / META runs):

  nonoverlap  n non-overlapping runs `w w`, separated by legal particles:
              `w0 w0 li w1 w1 e w2 w2 e ...` (valid, RESOLVED)
  overlap     n m12-style overlapping components `jan pali jan pali jan`
              (each has two valid folds) joined by `e`: 2^n genuine readings
  random      seeded random invalid sequences: n runs of 2-3 copies of a
              random unit, separated by random particles, ending in `li`
              (particle-last, so INVALID by construction)
  long203     the legal 203-token statement `jan li pali` + 100 x `e ilo`

Each case runs in a fresh subprocess with a hard wall-clock cap (default
20 s); a case that hits the cap is recorded as TIMEOUT and killed.
Environment variable BENCH_MAX_SECONDS overrides the parser's max_seconds budget.
A second subprocess measures peak traced memory (tracemalloc) unless the
time pass timed out.  The `openpona` package is whatever is importable in
the environment (use PYTHONPATH to point at a baseline tree); the module
path is recorded so the table says which tree was measured.

Usage:
  python tools/bench_meta.py [--cap 20] [--sizes 8,12,16,20] [--json out.json]
  python tools/bench_meta.py --print-case nonoverlap 8
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys

SEMANTIC_POOL = [
    "jan", "ilo", "sitelen", "pali", "lukin", "sona", "kama", "awen", "ijo",
    "nasin", "open", "ma", "lawa", "ken", "wile", "toki", "pana", "tenpo",
]
PARTICLES = ("li", "e", "pi", "anu", "la")
FAMILIES = ("nonoverlap", "overlap", "random")


def _words(n: int) -> list[str]:
    """n units, consecutive ones distinct (so particles always separate runs)."""
    return [SEMANTIC_POOL[i % len(SEMANTIC_POOL)] for i in range(n)]


def make_case(family: str, n: int, seed: int = 0) -> str:
    if family == "nonoverlap":
        w = _words(n)
        parts = [f"{w[0]} {w[0]}"]
        for i in range(1, n):
            parts.append(("li " if i == 1 else "e ") + f"{w[i]} {w[i]}")
        return " ".join(parts)
    if family == "overlap":
        comp = "jan pali jan pali jan"
        if n == 1:
            return comp
        return comp + " li " + " e ".join([comp] * (n - 1))
    if family == "random":
        rng = random.Random(f"bench_meta:{seed}:{n}")
        out: list[str] = []
        for i in range(n):
            out += [rng.choice(SEMANTIC_POOL)] * rng.choice((2, 3))
            out.append(rng.choice(PARTICLES) if i < n - 1 else "li")
        return " ".join(out)
    if family == "long203":
        return "jan li pali " + " ".join(["e ilo"] * 100)
    raise ValueError(family)


_CHILD = r"""
import json, os, sys, time, tracemalloc
import openpona
from openpona import Budget, parse
mode, text = sys.argv[1], sys.argv[2]
BUD = Budget(max_seconds=float(os.environ["BENCH_MAX_SECONDS"])) if "BENCH_MAX_SECONDS" in os.environ else Budget()
parse("jan li pali")  # warm the grammar cache outside the measured region
res = {"module": openpona.__file__}
if mode == "time":
    t0 = time.perf_counter()
    r = parse(text, BUD)
    res["seconds"] = time.perf_counter() - t0
    res["status"] = r.status
    res["n_skeletons"] = len(r.skeletons)
    res["reason"] = getattr(r, "reason", None)
    try:
        from openpona.parser import ParseStats
        st = ParseStats()
        parse(text, BUD, stats=st)
        res["work"] = st.work
    except Exception:
        res["work"] = None
else:
    tracemalloc.start()
    parse(text, BUD)
    res["peak_bytes"] = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
print(json.dumps(res))
"""


def _run(mode: str, text: str, cap: float) -> dict | None:
    try:
        proc = subprocess.run([sys.executable, "-c", _CHILD, mode, text],
                              capture_output=True, text=True, timeout=cap)
    except subprocess.TimeoutExpired:
        return None
    if proc.returncode != 0:
        return {"error": proc.stderr.strip().splitlines()[-1:] or ["?"]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def bench(sizes: list[int], cap: float, seed: int) -> list[dict]:
    cases = [(f, n) for f in FAMILIES for n in sizes] + [("long203", 203)]
    rows = []
    for fam, n in cases:
        text = make_case(fam, n, seed)
        row = {"family": fam, "n": n, "tokens": len(text.split())}
        t = _run("time", text, cap)
        if t is None:
            row.update(status="TIMEOUT", seconds=None, peak_bytes=None)
        elif "error" in t:
            row.update(status="ERROR", error=t["error"], seconds=None, peak_bytes=None)
        else:
            row.update(t)
            m = _run("mem", text, cap)
            row["peak_bytes"] = None if not m or "peak_bytes" not in m else m["peak_bytes"]
        rows.append(row)
        print(json.dumps(row), file=sys.stderr, flush=True)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=float, default=20.0, help="per-case wall-clock cap, seconds")
    ap.add_argument("--sizes", default="8,12,16,20")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", help="write rows to this file")
    ap.add_argument("--print-case", nargs=2, metavar=("FAMILY", "N"))
    a = ap.parse_args(argv)
    if a.print_case:
        print(make_case(a.print_case[0], int(a.print_case[1]), a.seed))
        return 0
    rows = bench([int(s) for s in a.sizes.split(",")], a.cap, a.seed)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)
    print("| family | n | tokens | status | time s | peak KiB | work |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        sec = "TIMEOUT" if r["status"] == "TIMEOUT" else (
            f"{r['seconds']:.4f}" if r.get("seconds") is not None else "-")
        mem = f"{r['peak_bytes'] / 1024:.0f}" if r.get("peak_bytes") is not None else "-"
        print(f"| {r['family']} | {r['n']} | {r['tokens']} | {r['status']} | {sec} | {mem} "
              f"| {r.get('work') if r.get('work') is not None else '-'} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
