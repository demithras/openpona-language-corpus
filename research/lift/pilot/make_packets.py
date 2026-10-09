"""Build the pilot allocation and one participant packet per isolated LLM run.

PILOT - EXPLORATORY, NOT CONFIRMATORY. Writes NO gold: packets carry labels, candidates,
glossary and trial ids only. Run `freeze.py` on the output directory before any response.

  python research/lift/pilot/make_packets.py --vendors a,b --per-arm-per-vendor 3 --seed 1 --out-dir DIR
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilotlib as pl  # noqa: E402

lift = pl.lift


def build_participants(vendors, k, seed):
    """Vendor x condition x k participants, shuffled once so pid order is not grouped by arm."""
    cells = [(v, c, j) for v in vendors for c in lift.CONDITIONS for j in range(k)]
    random.Random(pl.sub_seed(seed, "allocation")).shuffle(cells)
    width = max(3, len(str(len(cells))))
    return [{"participant_id": f"p{i + 1:0{width}d}", "vendor": v, "condition": c, "cell_index": j}
            for i, (v, c, j) in enumerate(cells)]


def orders(seed, part, tokens, trial_ids):
    """Counterbalance: members 2m and 2m+1 of a vendor x condition cell get the same shuffled
    candidate/trial order, forward for even and reversed for odd cell_index."""
    pair = part["cell_index"] // 2
    cand = list(tokens)
    random.Random(pl.sub_seed(seed, "cand", part["vendor"], part["condition"], pair)).shuffle(cand)
    trials = list(trial_ids)
    random.Random(pl.sub_seed(seed, "trial", part["vendor"], part["condition"], pair)).shuffle(trials)
    rev = part["cell_index"] % 2 == 1
    if rev:
        cand.reverse(); trials.reverse()
    return cand, trials, rev


def render_packet(public, cand, trials):
    rows, cols, gl = public["row_labels"], public["column_labels"], public["glossary"]
    L = []
    L.append("# Grid reconstruction exercise")
    L.append("")
    L.append("You are taking part in a short reconstruction exercise. A hidden grid of 6 rows and 7 columns "
             "holds one token in each of its 42 cells. You never see the grid. For each cell you get a trial id "
             "of the form R<row>C<column>, a row label and a column label. Choose, for each trial id, the one "
             "token from the candidate list that you think belongs in that cell, or leave it empty (\"\") if "
             "you do not want to answer.")
    L.append("")
    L.append("Rules: answer only from the text of this message. Do not use tools, web search, files, code "
             "execution or any other source, and do not ask questions. Use exactly the tokens as spelled in the "
             "candidate list.")
    L.append("")
    L.append("## Row labels")
    L.append("")
    for i, x in enumerate(rows, 1):
        L.append(f"- Row {i}: {x}")
    L.append("")
    L.append("## Column labels")
    L.append("")
    for i, x in enumerate(cols, 1):
        L.append(f"- Column {i}: {x}")
    L.append("")
    L.append("## Candidate tokens with their English definitions")
    L.append("")
    L.append("Definitions: lipu Linku, https://github.com/lipu-linku/sona, CC BY-SA 4.0 (retrieved 2026-10-09).")
    L.append("")
    for t in cand:
        L.append(f"- {t}: {gl[t]}")
    L.append("")
    L.append("## Trials")
    L.append("")
    for tid in trials:
        r, c = tid[1:].split("C")
        L.append(f"- {tid} = row {r}, column {c}")
    L.append("")
    L.append("## How to answer")
    L.append("")
    L.append("Reply with one JSON object in exactly this shape, inside one code block, with every trial id "
             "present exactly once. Put a candidate token between the quotes, or leave the quotes empty to abstain.")
    L.append("")
    L.append("```json")
    L.append("{")
    L.append('  "answers": [')
    for i, tid in enumerate(trials):
        L.append(f'    {{"trial_id": "{tid}", "token": ""}}' + ("," if i < len(trials) - 1 else ""))
    L.append("  ]")
    L.append("}")
    L.append("```")
    L.append("")
    L.append("## One last question (answer after the JSON block)")
    L.append("")
    L.append(f"{pl.FAMILIARITY_QUESTION}")
    L.append("")
    L.append("On a new line after the JSON block write exactly one of `FAMILIARITY: yes`, `FAMILIARITY: no`, "
             "`FAMILIARITY: unsure`, followed by one short sentence.")
    L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vendors", required=True, help="comma-separated vendor labels, e.g. a,b,c")
    ap.add_argument("--per-arm-per-vendor", type=int, default=3)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out-dir", "--out", "--dir", dest="out_dir", required=True)
    a = ap.parse_args(argv)
    try:
        vendors = [v.strip() for v in a.vendors.split(",") if v.strip()]
        if not vendors or len(set(vendors)) != len(vendors):
            raise ValueError("--vendors must be a non-empty list of distinct labels")
        if a.per_arm_per_vendor < 1:
            raise ValueError("--per-arm-per-vendor must be >= 1")
        out = Path(a.out_dir)
        if out.exists() and any(out.iterdir()):
            raise ValueError(f"{out} must be absent or empty")
        profile = lift.load_profile()
        grid = lift.validate(profile)
        tokens = sorted(grid.values())
        publics = {c: lift.make_materials(profile, c, a.seed)[0] for c in lift.CONDITIONS}
        trial_ids = sorted(f"R{r}C{c}" for r in range(1, 7) for c in range(1, 8))
        parts = build_participants(vendors, a.per_arm_per_vendor, a.seed)
        (out / "packets").mkdir(parents=True, exist_ok=True)
        (out / "responses").mkdir(exist_ok=True)
        rows = []
        for p in parts:
            cand, trials, rev = orders(a.seed, p, tokens, trial_ids)
            name = f"packets/{p['participant_id']}.md"
            (out / name).write_text(render_packet(publics[p["condition"]], cand, trials), encoding="utf-8")
            rows.append({**p, "reversed_order": int(rev), "packet": name})
        with open(out / pl.ALLOCATION_FILE, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=pl.ALLOCATION_FIELDS, lineterminator="\n")
            w.writeheader(); w.writerows(rows)
        cfg = {"banner": pl.BANNER, "seed": a.seed, "vendors": vendors, "per_arm_per_vendor": a.per_arm_per_vendor,
               "conditions": list(lift.CONDITIONS), "participants": len(rows), "profile_id": profile["profile_id"]}
        (out / pl.CONFIG_FILE).write_text(json.dumps(cfg, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PACKETS_WRITTEN", "participants": len(rows), "out_dir": str(out),
                          "next": "run freeze.py before any response"}, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, lift.DriftError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
