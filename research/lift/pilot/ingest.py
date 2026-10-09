"""Turn raw model replies (responses/<pid>.txt) into validated parsed/<pid>.json plus an exclusions log.

PILOT - EXPLORATORY, NOT CONFIRMATORY. Needs NO gold (never opens a private directory): it checks only
ids against the 42 public trial ids and tokens against the 42 public glossary tokens.

A reply is accepted only if exactly one distinct JSON object with an "answers" array is found (prose and
code fences around it are fine) and its trial ids are exactly the 42 expected ids: missing, duplicate and
foreign ids reject the whole reply. A rejected reply is NOT dropped silently: it is written to
ingest_log.json with its reason. Tokens must equal "" or a candidate token (surrounding whitespace is
trimmed; no other normalisation). The familiarity answer is recorded and never used to exclude.

  python research/lift/pilot/ingest.py --dir DIR
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilotlib as pl  # noqa: E402

lift = pl.lift
TRIAL_IDS = frozenset(f"R{r}C{c}" for r in range(1, 7) for c in range(1, 8))
FAM_RE = re.compile(r"^[ \t>*_`-]*FAMILIARITY[ \t*_`]*:[ \t*_`]*(yes|no|unsure)\b(.*)$", re.I | re.M)


class Reject(ValueError):
    def __init__(self, reason, detail=""):
        self.reason, self.detail = reason, detail
        super().__init__(f"{reason}: {detail}" if detail else reason)


def extract_answer_objects(text):
    """All top-level JSON objects in free text that carry an "answers" key."""
    dec, i, found = json.JSONDecoder(), 0, []
    while True:
        i = text.find("{", i)
        if i < 0:
            return found
        try:
            obj, end = dec.raw_decode(text, i)
        except ValueError:
            i += 1
            continue
        if isinstance(obj, dict) and "answers" in obj:
            found.append(obj)
        i = end


def parse_familiarity(text):
    ms = FAM_RE.findall(text)
    if not ms:
        return "missing", ""
    ans, rest = ms[-1]
    return ans.lower(), rest.strip()


def validate_reply(text, tokens):
    objs = extract_answer_objects(text)
    if not objs:
        raise Reject("no_json_answer_object")
    if any(o != objs[0] for o in objs[1:]):
        raise Reject("multiple_distinct_answer_objects", f"{len(objs)} found")
    rows = objs[0]["answers"]
    if not isinstance(rows, list):
        raise Reject("answers_not_a_list")
    seen = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("trial_id"), str) or not isinstance(row.get("token"), str):
            raise Reject("malformed_entry", f"entry {i}: {json.dumps(row, ensure_ascii=False)[:80]}")
        tid, tok = row["trial_id"].strip(), row["token"].strip()
        if tid not in TRIAL_IDS:
            raise Reject("foreign_trial_id", tid)
        if tid in seen:
            raise Reject("duplicate_trial_id", tid)
        if tok != "" and tok not in tokens:
            raise Reject("foreign_token", f"{tid}={tok!r}")
        seen[tid] = tok
    if set(seen) != TRIAL_IDS:
        raise Reject("missing_trial_id", ",".join(sorted(TRIAL_IDS - set(seen))))
    return seen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", "--out-dir", dest="dir", required=True)
    a = ap.parse_args(argv)
    d = Path(a.dir)
    try:
        problems = pl.verify_freeze(d)
        if problems:
            raise ValueError("pilot freeze check failed, refusing to ingest: " + "; ".join(problems[:5]))
        fz_mtime = (d / pl.FREEZE_FILE).stat().st_mtime
        tokens = set(lift.load_glossary(lift.validate(lift.load_profile())))
        alloc = {r["participant_id"]: r for r in pl.read_allocation(d)}
        (d / "parsed").mkdir(exist_ok=True)
        accepted, excluded, flags = [], [], []
        raw_files = {p.stem: p for p in sorted((d / "responses").glob("*.txt")) if not p.name.endswith(".thinking.txt")}
        for pid in sorted(set(raw_files) - set(alloc)):
            excluded.append({"participant_id": pid, "reason": "unknown_participant_id", "detail": raw_files[pid].name})
        for pid, row in alloc.items():
            if pid not in raw_files:
                continue
            raw = raw_files[pid].read_bytes()
            text = raw.decode("utf-8", errors="replace")
            try:
                answers = validate_reply(text, tokens)
            except Reject as exc:
                excluded.append({"participant_id": pid, "vendor": row["vendor"], "condition": row["condition"],
                                 "reason": exc.reason, "detail": exc.detail, "raw_sha256": pl.sha256_bytes(raw)})
                continue
            fam, fam_text = parse_familiarity(text)
            meta_path = d / "responses" / f"{pid}.meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else None
            if raw_files[pid].stat().st_mtime < fz_mtime:
                flags.append({"participant_id": pid, "flag": "response_file_older_than_freeze"})
            if meta is None:
                flags.append({"participant_id": pid, "flag": "no_meta_json (vendor/model id/date/settings not recorded)"})
            rec = {"participant_id": pid, "vendor": row["vendor"], "condition": row["condition"],
                   "profile_id": lift.load_profile()["profile_id"], "raw_sha256": pl.sha256_bytes(raw),
                   "familiarity_answer": fam, "familiarity_text": fam_text, "meta": meta,
                   "answers": [{"trial_id": t, "token": answers[t]} for t in sorted(answers)]}
            (d / "parsed" / f"{pid}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            accepted.append(pid)
        # a stale parsed file for a participant that is no longer accepted must not feed the analysis
        for p in (d / "parsed").glob("*.json"):
            if p.stem not in accepted:
                p.unlink()
        log = {"banner": pl.BANNER, "accepted": accepted, "excluded": excluded, "flags": flags,
               "allocated_without_response": sorted(set(alloc) - set(raw_files))}
        (d / "ingest_log.json").write_text(json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "INGESTED", "accepted": len(accepted), "excluded": len(excluded),
                          "allocated_without_response": len(log["allocated_without_response"])}, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, lift.DriftError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
