"""Blind Externalized Lift trial preparation and scoring; no scientific results embedded.

Python >=3.11, standard library only. DO NOT give full source package or private gold
files to participants. Profile tokens are gold lookup, NOT a lexical generator.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import sys

PROFILE = Path(__file__).with_name("coordinates.v0.1.json")
GLOSSARY = Path(__file__).with_name("glossary") / "linku_en_2026-10-09.json"
STRUCTURAL = ["li", "la", "e", "tan", "pi", "anu"]
ROW5 = ["sitelen", "linja", "pana", "toki", "tenpo", "pini", "pi"]
CONDITIONS = ("external", "embedded", "generic", "shuffled")


def load_profile(path=PROFILE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class DriftError(ValueError):
    """Profile drift with a stable machine-readable reason name."""
    def __init__(self, kind, detail=""):
        self.kind = kind
        super().__init__(f"{kind}: {detail}" if detail else kind)


def find_matrix():
    here = Path(__file__).resolve().parents[2] / "data" / "matrix.csv"
    for cand in (here, Path.cwd() / "data" / "matrix.csv"):
        if cand.is_file():
            return cand
    raise DriftError("matrix_not_found", "data/matrix.csv not located")


def load_matrix(path=None):
    """Read repo data/matrix.csv -> {(row, col): token}; fail with a named reason."""
    path = Path(path) if path else find_matrix()
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    grid = {}
    for x in rows:
        key = (int(x["row"]), int(x["column"]))
        if key in grid:
            raise DriftError("matrix_csv_duplicate_cell", str(key))
        grid[key] = x["token"]
    if len(grid) != 42 or len(set(grid.values())) != 42:
        raise DriftError("matrix_csv_not_bijective", f"{len(grid)} cells, {len(set(grid.values()))} tokens")
    if set(grid) != {(r, c) for r in range(1, 7) for c in range(1, 8)}:
        raise DriftError("matrix_csv_incomplete_grid")
    return grid


def validate(profile, matrix=None):
    """Validate profile; token cells are checked against data/matrix.csv.

    Raises DriftError whose .kind names the drift: missing_slot, duplicate_token,
    structural_column_drift, row_five_drift, matrix_token_mismatch, plus label/id kinds.
    """
    if profile.get("profile_id") != "externalized-lift-0.1":
        raise DriftError("wrong_profile_id")
    rs, cs, cells = profile["row_archetypes"], profile["column_operations"], profile["cells"]
    if [r["id"] for r in rs] != [f"R{i}" for i in range(1, 7)]: raise DriftError("row_ids")
    if [c["id"] for c in cs] != [f"C{i}" for i in range(1, 8)]: raise DriftError("column_ids")
    if [x["label"] for x in rs] != ["Process", "Inquiry", "Method", "Agency", "Representation", "Integration"]: raise DriftError("row_labels")
    if [x["label"] for x in cs] != ["Identity", "Ground", "Transform", "Select", "Realize", "Evaluate", "Structure"]: raise DriftError("column_labels")
    if len(cells) != 42: raise DriftError("missing_slot", f"{len(cells)} cells, expected 42")
    seen, tokens, grid = set(), set(), {}
    for x in cells:
        r, c, t = x["row"], x["col"], x["token"]
        if not (type(r) is int and type(c) is int and 1 <= r <= 6 and 1 <= c <= 7): raise DriftError("invalid_coordinates", str(x))
        if x["coord"] != f"R{r}C{c}": raise DriftError("mislabelled_cell", str(x))
        if (r, c) in seen: raise DriftError("duplicate_slot", x["coord"])
        if t in tokens: raise DriftError("duplicate_token", t)
        seen.add((r, c)); tokens.add(t); grid[(r, c)] = t
    if seen != {(r, c) for r in range(1, 7) for c in range(1, 8)}: raise DriftError("missing_slot", "incomplete grid")
    if [grid[(r, 7)] for r in range(1, 7)] != STRUCTURAL: raise DriftError("structural_column_drift")
    if [grid[(5, c)] for c in range(1, 8)] != ROW5: raise DriftError("row_five_drift")
    canon = matrix if matrix is not None else load_matrix()
    if grid != canon:
        bad = sorted(f"R{r}C{c}" for (r, c) in grid if grid[(r, c)] != canon[(r, c)])
        raise DriftError("matrix_token_mismatch", "differs from data/matrix.csv at " + ",".join(bad))
    return grid


def load_glossary(grid, path=GLOSSARY):
    """Frozen candidate glossary {token: definition}; must cover exactly the 42 matrix tokens."""
    g = json.loads(Path(path).read_text(encoding="utf-8"))
    defs = g["definitions"]
    if set(defs) != set(grid.values()):
        missing = sorted(set(grid.values()) - set(defs)); extra = sorted(set(defs) - set(grid.values()))
        raise DriftError("glossary_token_mismatch", f"missing={missing} extra={extra}")
    if any(not isinstance(v, str) or not v.strip() for v in defs.values()):
        raise DriftError("glossary_empty_definition")
    return dict(sorted(defs.items()))


def dirs_overlap(a, b):
    """True when two directories are equal or one lies inside the other (symlinks resolved)."""
    a, b = Path(a).resolve(), Path(b).resolve()
    return a == b or a in b.parents or b in a.parents


def canonical_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(obj):
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def make_materials(profile, condition, seed):
    if condition not in CONDITIONS: raise ValueError("unknown condition")
    grid = validate(profile)
    rng = random.Random(seed)
    rows=[r["label"] for r in profile["row_archetypes"]]
    cols=[c["label"] for c in profile["column_operations"]]
    if condition == "embedded":
        rows=[grid[(r,1)] for r in range(1,7)]
        cols=[grid[(1,c)] for c in range(1,8)]
    elif condition == "generic":
        rows=[f"R{r}" for r in range(1,7)]
        cols=[f"C{c}" for c in range(1,8)]
    elif condition == "shuffled":
        # One fixed derangement per axis; no same-axis identity retained.
        rows=rows[1:]+rows[:1]
        cols=cols[1:]+cols[:1]
    # Candidate list contains lexicon but no coordinate-token association.
    choices=sorted(grid.values())
    rng.shuffle(choices)
    trials=[]
    for r in range(1,7):
        for c in range(1,8):
            # Labels live in axis lists, not inside trial records, so no trial record sits next to a token.
            trials.append({"trial_id":f"R{r}C{c}","row_index":r,"column_index":c,"is_primary_interior":r>1 and c>1})
    rng.shuffle(trials)
    shared={"profile_id":profile["profile_id"],"condition":condition,"seed":seed}
    public={**shared,"instructions":"For each trial choose one token from candidates using ONLY the row label (row_labels[row_index-1]) and column label (column_labels[column_index-1]) of its trial. Respond with one token or empty string; no access to gold table.","row_labels":rows,"column_labels":cols,"candidate_tokens":choices,"glossary":load_glossary(grid),"trials":trials}
    gold={**shared,"gold":{f"R{r}C{c}":grid[(r,c)] for r in range(1,7) for c in range(1,8)}}
    template={**shared,"answers":[{"trial_id":t["trial_id"],"token":""} for t in trials]}
    return public, template, gold


def read_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def dump_json(path, obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")


def validate_answers(gold, submission):
    if submission.get("profile_id") != gold.get("profile_id") or submission.get("condition") != gold.get("condition"):
        raise ValueError("submission metadata mismatches gold")
    rows=submission.get("answers")
    if not isinstance(rows,list): raise ValueError("answers not an array")
    seen={}; vocabulary=set(gold["gold"].values())
    for row in rows:
        trial=row.get("trial_id")
        token=row.get("token")
        if trial in seen: raise ValueError(f"duplicate trial {trial}")
        if trial not in gold["gold"]: raise ValueError(f"unknown trial {trial}")
        if token != "" and token not in vocabulary: raise ValueError(f"unknown token {token}")
        seen[trial]=token
    if set(seen)!=set(gold["gold"]): raise ValueError("missing trials: " + ",".join(sorted(set(gold["gold"])-set(seen))))
    return seen


def score(gold, submission):
    actual=validate_answers(gold,submission)
    totals={"interior":{"n":0,"correct":0},"edge":{"n":0,"correct":0},"all":{"n":0,"correct":0},"interior_no_c7":{"n":0,"correct":0},"c7_interior":{"n":0,"correct":0}}
    wrong=[]
    for trial,truth in sorted(gold["gold"].items()):
        coord=trial.split('C'); r=int(coord[0][1:]); c=int(coord[1]);
        sector="interior" if r>1 and c>1 else "edge"
        matched=(actual[trial]==truth)
        kinds=[sector,"all"]
        if sector=="interior": kinds.append("c7_interior" if c==7 else "interior_no_c7")
        for kind in kinds:
            totals[kind]["n"]+=1; totals[kind]["correct"]+=int(matched)
        if not matched: wrong.append({"trial_id":trial,"actual":actual[trial],"expected":truth})
    for x in totals.values(): x["accuracy"]=round(x["correct"]/x["n"],8)
    return {"profile_id":gold["profile_id"],"condition":gold["condition"],"seed":gold.get("seed"),"scoring":"Top-1 exact; omissions require blank token and are incorrect","totals":totals,"mistakes":wrong}


def label_permutation_null(gold,submission,reps,seed):
    if reps<1: raise ValueError("reps must be >=1")
    actual=validate_answers(gold,submission)
    truths=gold["gold"]
    ids=sorted(truths)
    observed=sum(actual[k]==truths[k] for k in ids if int(k.split('C')[0][1:])>1 and int(k.split('C')[1])>1)
    tokens=[truths[k] for k in ids]
    rng=random.Random(seed)
    num_ge=0; counts={}
    for _ in range(reps):
        vals=tokens.copy(); rng.shuffle(vals)
        n=sum(actual[k]==v for k,v in zip(ids,vals) if int(k.split('C')[0][1:])>1 and int(k.split('C')[1])>1)
        counts[str(n)]=counts.get(str(n),0)+1
        num_ge+=int(n>=observed)
    return {"test":"random bijective token-label assignment (NOT participant-arm inference)","interior_observed_correct":observed,"interior_n":30,"repetitions":reps,"seed":seed,"null_histogram":counts,"p_ge_plus_one":round((num_ge+1)/(reps+1),8)}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    v=sub.add_parser("validate"); v.add_argument("profile",nargs="?"); v.add_argument("--matrix")
    b=sub.add_parser("prepare"); b.add_argument("--condition",required=True,choices=CONDITIONS); b.add_argument("--seed",type=int,required=True); b.add_argument("--public-dir",required=True); b.add_argument("--private-dir",required=True)
    s=sub.add_parser("score"); s.add_argument("--gold",required=True); s.add_argument("--answers",required=True); s.add_argument("--out",required=True)
    n=sub.add_parser("null"); n.add_argument("--gold",required=True); n.add_argument("--answers",required=True); n.add_argument("--out",required=True); n.add_argument("--reps",type=int,default=10000); n.add_argument("--seed",type=int,required=True)
    args=p.parse_args(argv)
    try:
        if args.command=="validate":
            data=load_profile(args.profile) if args.profile else load_profile()
            validate(data, load_matrix(args.matrix) if args.matrix else None)
            print(json.dumps({"profile_id":data["profile_id"],"cell_count":42,"profile_sha256":digest(data),"matrix_checked":"data/matrix.csv","status":"PASS"},sort_keys=True));return 0
        if args.command=="prepare":
            pubdir,privdir=Path(args.public_dir),Path(args.private_dir)
            if dirs_overlap(pubdir,privdir): raise ValueError("public-dir and private-dir must be different and neither may lie inside the other (prereg point 9)")
            for d in (pubdir,privdir):
                if d.exists() and any(d.iterdir()): raise ValueError(f"{d} must be absent/empty to avoid overwriting files")
            pub,subm,gold=make_materials(load_profile(),args.condition,args.seed)
            dump_json(pubdir/"public_prompt.json",pub);dump_json(pubdir/"submission_template.json",subm);dump_json(privdir/"private_gold.json",gold)
            print(json.dumps({"status":"PREPARED_ONLY_NO_EXPERIMENT_RUN","public_sha256":digest(pub),"private_gold_file":str(privdir/"private_gold.json"),"warning":"KEEP GOLD SECRET; distribute only public-dir"},sort_keys=True));return 0
        if args.command=="score":
            report=score(read_json(args.gold),read_json(args.answers))
        else:
            report=label_permutation_null(read_json(args.gold),read_json(args.answers),args.reps,args.seed)
        dump_json(args.out,report);print(json.dumps({"status":"OK","output":args.out},sort_keys=True));return 0
    except DriftError as exc:
        print(f"DRIFT[{exc.kind}]: {exc}",file=sys.stderr);return 3
    except (ValueError,KeyError,OSError,TypeError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr);return 2

if __name__=='__main__': sys.exit(main())
