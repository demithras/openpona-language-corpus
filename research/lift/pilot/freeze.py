"""Write pilot_freeze.json (SHA-256 of profile, glossary, scorer, pilot scripts, packets, allocation, seed).

PILOT - EXPLORATORY, NOT CONFIRMATORY. Must run BEFORE any response is collected:
it refuses when responses/ already holds a file or when pilot_freeze.json exists.

  python research/lift/pilot/freeze.py --dir DIR           # write the freeze
  python research/lift/pilot/freeze.py --dir DIR --check   # verify only (exit 0 iff unchanged)
"""
from __future__ import annotations
import argparse
import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilotlib as pl  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", "--out-dir", dest="dir", required=True)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    d = Path(a.dir)
    try:
        if a.check:
            problems = pl.verify_freeze(d)
            for x in problems:
                print(f"CHANGED: {x}", file=sys.stderr)
            print(json.dumps({"status": "FREEZE_OK" if not problems else "FREEZE_BROKEN", "changed": len(problems)}))
            return 0 if not problems else 3
        if not (d / pl.ALLOCATION_FILE).is_file() or not (d / "packets").is_dir():
            raise ValueError(f"{d} is not a make_packets.py output directory")
        if (d / pl.FREEZE_FILE).exists():
            raise ValueError(f"{pl.FREEZE_FILE} already exists; a frozen pilot is never re-frozen in place")
        early = sorted(x.name for x in (d / "responses").glob("*") if x.is_file()) if (d / "responses").is_dir() else []
        if early:
            raise ValueError("responses already present, freeze must precede every response: " + ", ".join(early))
        fz = {"banner": pl.BANNER,
              "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "hashes": pl.compute_freeze(d)}
        (d / pl.FREEZE_FILE).write_text(json.dumps(fz, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "FROZEN", "file": str(d / pl.FREEZE_FILE), "packets": len(fz["hashes"]["packets"]),
                          "seed": fz["hashes"]["seed"]}, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
