"""Exploratory pilot analysis. Writes report.md + results.json headed 'PILOT - EXPLORATORY, NOT CONFIRMATORY'.

Refuses to run if the pilot_freeze.json hashes (profile, glossary, scorer, pilot scripts, packets, allocation,
seed) no longer match the files on disk. Gold is read ONLY here, from --gold (a private_gold.json written by
`blind_experiment.py prepare --private-dir`, or a directory searched recursively for private_gold.json).

Per participant: Top-1 on interior 30 / edge 12 / all 42, plus sensitivity sectors interior_no_c7 (25) and c7_interior (5) (abstention counts as wrong). Per arm: mean of the
participant scores with a participant-level percentile bootstrap 95% CI (fixed seed, no binomial formula),
per-cell confusion, and per participant the existing label-permutation null (a label-symmetry null, not an
arm test).

  python research/lift/pilot/analyze.py --dir DIR --gold PRIVATE_DIR_OR_FILE
"""
from __future__ import annotations
import argparse
import json
import random
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilotlib as pl  # noqa: E402

lift = pl.lift
SECTORS = ("interior", "edge", "all", "interior_no_c7", "c7_interior")


def load_gold(path):
    p = Path(path)
    files = [p] if p.is_file() else sorted(p.rglob("private_gold.json"))
    if not files:
        raise ValueError(f"no private_gold.json under {p}")
    docs = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    maps = [d["gold"] for d in docs]
    if any(m != maps[0] for m in maps[1:]):
        raise ValueError("private gold files disagree with each other")
    canon = {f"R{r}C{c}": t for (r, c), t in lift.load_matrix().items()}
    if maps[0] != canon:
        raise ValueError("private gold differs from data/matrix.csv")
    return docs[0]


def participant_scores(rec, gold_doc, null_reps, seed):
    sub = {"profile_id": gold_doc["profile_id"], "condition": gold_doc["condition"], "answers": rec["answers"]}
    g = {**gold_doc}
    rep = lift.score(g, sub)
    t = rep["totals"]
    null = lift.label_permutation_null(g, sub, null_reps, pl.sub_seed(seed, "null", rec["participant_id"]))
    return {"participant_id": rec["participant_id"], "vendor": rec["vendor"], "condition": rec["condition"],
            "familiarity": rec["familiarity_answer"],
            **{f"{s}_correct": t[s]["correct"] for s in SECTORS}, **{f"{s}_n": t[s]["n"] for s in SECTORS},
            **{f"{s}_top1": t[s]["accuracy"] for s in SECTORS},
            "abstained": sum(1 for a in rec["answers"] if a["token"] == ""),
            "null_p_ge_plus_one_interior": null["p_ge_plus_one"], "null_reps": null["repetitions"],
            "mistakes": rep["mistakes"]}


def fmt(x):
    return "n/a" if x is None else f"{x:.3f}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", "--out-dir", dest="dir", required=True)
    ap.add_argument("--gold", "--private-dir", "--gold-dir", dest="gold", required=True)
    ap.add_argument("--seed", type=int, default=pl.DEFAULT_BOOT_SEED, help="bootstrap / permutation-null seed")
    ap.add_argument("--boot-reps", type=int, default=10000)
    ap.add_argument("--null-reps", type=int, default=10000)
    a = ap.parse_args(argv)
    d = Path(a.dir)
    try:
        problems = pl.verify_freeze(d)
        if problems:
            raise ValueError("pilot freeze check failed, refusing to analyse: " + "; ".join(problems[:5]))
        gold_doc = load_gold(a.gold)
        recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((d / "parsed").glob("*.json"))]
        if not recs:
            raise ValueError("no parsed responses: run ingest.py first")
        log = json.loads((d / "ingest_log.json").read_text(encoding="utf-8")) if (d / "ingest_log.json").is_file() else {}
        people = [participant_scores(r, gold_doc, a.null_reps, a.seed) for r in recs]
        cond_order = [c for c in lift.CONDITIONS if any(p["condition"] == c for p in people)]
        arms = {}
        for c in cond_order:
            ps = [p for p in people if p["condition"] == c]
            arm = {"n_participants": len(ps)}
            for s in SECTORS:
                vals = [p[f"{s}_top1"] for p in ps]
                arm[s] = {"mean_top1": sum(vals) / len(vals), "sd": statistics.stdev(vals) if len(vals) > 1 else None,
                          "ci95_participant_bootstrap": pl.bootstrap_ci(vals, a.boot_reps, pl.sub_seed(a.seed, "boot", c, s)),
                          "min": min(vals), "max": max(vals)}
            arm["by_vendor_interior_mean"] = {v: statistics.mean(p["interior_top1"] for p in ps if p["vendor"] == v)
                                              for v in sorted({p["vendor"] for p in ps})}
            conf = {}
            for tid, truth in sorted(gold_doc["gold"].items()):
                cnt = {}
                for r in recs:
                    if r["condition"] == c:
                        tok = next(x["token"] for x in r["answers"] if x["trial_id"] == tid)
                        cnt[tok] = cnt.get(tok, 0) + 1
                conf[tid] = {"gold": truth, "answers": dict(sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))),
                             "correct": cnt.get(truth, 0), "n": len(ps)}
            arm["per_cell_confusion"] = conf
            arms[c] = arm
        contrasts = {}
        if "external" in arms:
            for sec in ("interior", "interior_no_c7"):
                ext = [p[f"{sec}_top1"] for p in people if p["condition"] == "external"]
                for c in cond_order:
                    if c == "external":
                        continue
                    oth = [p[f"{sec}_top1"] for p in people if p["condition"] == c]
                    diffs = None
                    if ext and oth:
                        # interior keeps its original seed label so existing values are unchanged
                        rng = random.Random(pl.sub_seed(a.seed, "contrast", c) if sec == "interior"
                                            else pl.sub_seed(a.seed, "contrast", c, sec))
                        ds = sorted(sum(rng.choices(ext, k=len(ext))) / len(ext) - sum(rng.choices(oth, k=len(oth))) / len(oth)
                                    for _ in range(a.boot_reps))
                        diffs = [ds[int(0.025 * a.boot_reps)], ds[int(0.975 * a.boot_reps) - 1]]
                    contrasts[f"external_minus_{c}_{sec}"] = {
                        "difference_of_means": (sum(ext) / len(ext) - sum(oth) / len(oth)) if ext and oth else None,
                        "ci95_independent_participant_bootstrap": diffs}
        fam = {}
        for p in people:
            fam.setdefault(p["condition"], {}).setdefault(p["familiarity"], 0)
            fam[p["condition"]][p["familiarity"]] += 1
        results = {"banner": pl.BANNER, "freeze_verified": True, "seed": a.seed, "boot_reps": a.boot_reps,
                   "null_reps": a.null_reps, "n_participants_analysed": len(people),
                   "ingest_excluded": log.get("excluded", []), "ingest_flags": log.get("flags", []),
                   "allocated_without_response": log.get("allocated_without_response", []),
                   "participants": [{k: v for k, v in p.items()} for p in people],
                   "arms": arms, "contrasts": contrasts, "familiarity_counts_by_arm": fam,
                   "notes": ["Abstention counts as incorrect.", "Familiarity answers are reported, never used to exclude.",
                             "The null is a label-permutation (label-symmetry) null per participant, not an arm test.",
                             "Lift labels have been public on GitHub since 2026-10-09: training/browsing exposure cannot be excluded.",
                             "Pilot only: it sizes the main study and is not a confirmatory sample."]}
        (d / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        R = [f"# {pl.BANNER}", "",
             f"Participants analysed: {len(people)}; excluded at ingest: {len(results['ingest_excluded'])}; "
             f"allocated without response: {len(results['allocated_without_response'])}. Freeze verified. "
             f"Abstention counts as wrong. Bootstrap/null seed {a.seed}.", "",
             "## Per arm (mean of participant Top-1, participant-level bootstrap 95% CI)", "",
             "| arm | n | interior 30 | interior 95% CI | interior w/o C7 (25) | interior w/o C7 95% CI | C7 (5) | C7 95% CI | edge 12 | all 42 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
        for c, arm in arms.items():
            ci = arm["interior"]["ci95_participant_bootstrap"]
            n7, c7 = arm["interior_no_c7"], arm["c7_interior"]
            R.append(f"| {c} | {arm['n_participants']} | {fmt(arm['interior']['mean_top1'])} | [{fmt(ci[0])}, {fmt(ci[1])}] | "
                     f"{fmt(n7['mean_top1'])} | [{fmt(n7['ci95_participant_bootstrap'][0])}, {fmt(n7['ci95_participant_bootstrap'][1])}] | "
                     f"{fmt(c7['mean_top1'])} | [{fmt(c7['ci95_participant_bootstrap'][0])}, {fmt(c7['ci95_participant_bootstrap'][1])}] | "
                     f"{fmt(arm['edge']['mean_top1'])} | {fmt(arm['all']['mean_top1'])} |")
        R += ["", "## Per participant", "",
              "| participant | vendor | arm | interior /30 | edge /12 | all /42 | abstained | null p (interior) | familiarity |",
              "|---|---|---|---|---|---|---|---|---|"]
        for p in people:
            R.append(f"| {p['participant_id']} | {p['vendor']} | {p['condition']} | {p['interior_correct']} | {p['edge_correct']} | "
                     f"{p['all_correct']} | {p['abstained']} | {p['null_p_ge_plus_one_interior']} | {p['familiarity']} |")
        if contrasts:
            R += ["", "## External minus control, interior and interior w/o C7 (descriptive)", ""]
            for k, v in contrasts.items():
                ci = v["ci95_independent_participant_bootstrap"]
                R.append(f"- {k}: {fmt(v['difference_of_means'])}" + (f" [{fmt(ci[0])}, {fmt(ci[1])}]" if ci else ""))
        R += ["", "## Per-cell correct counts by arm (rows R1-R6, columns C1-C7; full confusion in results.json)", ""]
        for c, arm in arms.items():
            R += [f"### {c} (n={arm['n_participants']})", "", "| | C1 | C2 | C3 | C4 | C5 | C6 | C7 |", "|---|---|---|---|---|---|---|---|"]
            for r in range(1, 7):
                R.append(f"| R{r} | " + " | ".join(str(arm["per_cell_confusion"][f"R{r}C{k}"]["correct"]) for k in range(1, 8)) + " |")
            R.append("")
        R += ["## Familiarity (reported, not used to exclude)", "", "```", json.dumps(fam, sort_keys=True), "```", "",
              "## Limits", ""] + [f"- {n}" for n in results["notes"]]
        if results["ingest_excluded"] or results["ingest_flags"]:
            R += ["", "## Ingest exclusions and flags", "", "```", json.dumps({"excluded": results["ingest_excluded"], "flags": results["ingest_flags"]}, indent=1), "```"]
        (d / "report.md").write_text("\n".join(R) + "\n", encoding="utf-8")
        print(json.dumps({"status": "ANALYSED", "participants": len(people), "report": str(d / "report.md"), "results": str(d / "results.json")}, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, lift.DriftError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
