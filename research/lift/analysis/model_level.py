"""Model-level analysis of the Lift pilot (stdlib only).

Unit of analysis: the model (vendor). Runs of one model are not independent, so each model's mean over its
runs is its single score per arm. Reads only the results.json written by research/lift/pilot/analyze.py
(uses its `participants` list: vendor, condition, <sector>_top1). Writes model_level.json + model_level.md.

  python research/lift/analysis/model_level.py --results RESULTS.json --out-dir DIR [--seed N]
"""
from __future__ import annotations
import argparse
import json
import random
import sys
from math import comb
from pathlib import Path

BANNER = "PILOT - EXPLORATORY, NOT CONFIRMATORY - unit of analysis: model (runs are not independent)"
SECTORS = ("interior", "interior_no_c7", "c7_interior", "edge", "all")
CONTROLS = ("embedded", "generic", "shuffled")
DEFAULT_SEED = 20261009
BOOT_REPS = 10000


def sign_test_p(k, m_nonzero):
    """Exact one-sided P(X >= k | Bin(m_nonzero, 0.5))."""
    if m_nonzero == 0:
        return None
    return sum(comb(m_nonzero, i) for i in range(k, m_nonzero + 1)) / 2 ** m_nonzero


def boot_ci(vals, reps, seed):  # seed: any str/int
    rng = random.Random(seed)
    ms = sorted(sum(rng.choices(vals, k=len(vals))) / len(vals) for _ in range(reps))
    return [ms[int(0.025 * reps)], ms[int(0.975 * reps) - 1]]


def analyse(results, seed=DEFAULT_SEED, reps=BOOT_REPS):
    people = results["participants"]
    models = sorted({p["vendor"] for p in people})
    M = len(models)
    scores = {}
    for sec in SECTORS:
        scores[sec] = {}
        for v in models:
            scores[sec][v] = {}
            for arm in sorted({p["condition"] for p in people}):
                vals = [p[f"{sec}_top1"] for p in people if p["vendor"] == v and p["condition"] == arm]
                if vals:
                    scores[sec][v][arm] = {"mean": sum(vals) / len(vals), "n_runs": len(vals)}
    out = {"banner": BANNER, "seed": seed, "boot_reps": reps, "n_models": M, "models": models,
           "per_model_arm": scores, "contrasts": {}}
    for sec in SECTORS:
        for ctl in CONTROLS:
            per = {}
            for v in models:
                a = scores[sec][v]
                if "external" in a and ctl in a:
                    per[v] = a["external"]["mean"] - a[ctl]["mean"]
            if not per:
                continue
            d = list(per.values())
            m = len(d)
            pos, neg, tie = (sum(1 for x in d if x > 1e-12), sum(1 for x in d if x < -1e-12),
                             sum(1 for x in d if abs(x) <= 1e-12))
            notes = [f"Minimum attainable one-sided sign-test p with {pos + neg} non-tied models is "
                     f"{0.5 ** (pos + neg):.4g}" + (" (0.125 with M=3)." if pos + neg == 3 else ".")]
            if m < 5:
                notes.append(f"M={m} < 5: the bootstrap interval is not interpretable as a population CI.")
            out["contrasts"][f"external_minus_{ctl}_{sec}"] = {
                "sector": sec, "control": ctl, "per_model": per, "M": m, "k_positive": pos, "k_negative": neg,
                "k_tied": tie, "sign_test_p_one_sided": sign_test_p(pos, pos + neg),
                "mean_contrast": sum(d) / m,
                "ci95_model_bootstrap": boot_ci(d, reps, f"{seed}|{sec}|{ctl}"),
                "notes": notes}
    return out


def fmt(x):
    return "n/a" if x is None else f"{x:.3f}"


def render(out):
    R = [f"# {BANNER}", "",
         f"Models: {out['n_models']} ({', '.join(out['models'])}). Model score per arm = mean of that model's runs. "
         f"Bootstrap resamples models with replacement, seed {out['seed']}, {out['boot_reps']} reps.", ""]
    for sec in SECTORS:
        R += [f"## Sector: {sec}", "", "| model | arm | mean | n_runs |", "|---|---|---|---|"]
        for v in out["models"]:
            for arm, s in scores_items(out, sec, v):
                R.append(f"| {v} | {arm} | {fmt(s['mean'])} | {s['n_runs']} |")
        R += ["", "| contrast | per-model | k>0 / k<0 / ties of M | sign-test p (1-sided) | mean | model-bootstrap 95% CI |",
              "|---|---|---|---|---|---|"]
        for k, c in out["contrasts"].items():
            if c["sector"] != sec:
                continue
            pm = ", ".join(f"{v}: {x:+.3f}" for v, x in c["per_model"].items())
            R.append(f"| {k} | {pm} | {c['k_positive']} / {c['k_negative']} / {c['k_tied']} of {c['M']} | "
                     f"{fmt(c['sign_test_p_one_sided'])} | {fmt(c['mean_contrast'])} | "
                     f"[{fmt(c['ci95_model_bootstrap'][0])}, {fmt(c['ci95_model_bootstrap'][1])}] |")
        notes = sorted({n for c in out["contrasts"].values() if c["sector"] == sec for n in c["notes"]})
        R += [""] + [f"- {n}" for n in notes] + [""]
    R += ["## Limits", "", "- Run-level CIs in analyze.py are descriptive only; conclusions need agreement across models on interior_no_c7.",
          "- Ties are counted separately and excluded from the sign test."]
    return "\n".join(R) + "\n"


def scores_items(out, sec, v):
    return sorted(out["per_model_arm"][sec][v].items())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    a = ap.parse_args(argv)
    try:
        results = json.loads(Path(a.results).read_text(encoding="utf-8"))
        out = analyse(results, a.seed)
        d = Path(a.out_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / "model_level.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        (d / "model_level.md").write_text(render(out), encoding="utf-8")
        print(json.dumps({"status": "ANALYSED", "models": out["n_models"], "out": str(d)}))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
