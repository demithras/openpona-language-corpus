"""Shared helpers for the Lift pilot operator kit (stdlib only).

PILOT - EXPLORATORY, NOT CONFIRMATORY. Nothing here is a result.
"""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
LIFT_DIR = HERE.parent
REPO = LIFT_DIR.parents[1]
BANNER = "PILOT - EXPLORATORY, NOT CONFIRMATORY"
FAMILIARITY_QUESTION = "Before this task, had you seen a language or table called OpenPona or this 6x7 arrangement?"
FAMILIARITY_VALUES = ("yes", "no", "unsure")
FREEZE_FILE = "pilot_freeze.json"
ALLOCATION_FILE = "allocation.csv"
CONFIG_FILE = "pilot_config.json"
ALLOCATION_FIELDS = ["participant_id", "vendor", "condition", "cell_index", "reversed_order", "packet"]
DEFAULT_BOOT_SEED = 20261009


def _load_harness():
    spec = importlib.util.spec_from_file_location("lift_harness_for_pilot", LIFT_DIR / "blind_experiment.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lift = _load_harness()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def sub_seed(*parts) -> int:
    """Deterministic integer seed derived from arbitrary parts (independent of PYTHONHASHSEED)."""
    h = hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


def read_allocation(pdir):
    with open(Path(pdir) / ALLOCATION_FILE, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def pilot_script_paths():
    return sorted(HERE.glob("*.py"))


def rel_to_repo(p: Path) -> str:
    return str(Path(p).resolve().relative_to(REPO))


def compute_freeze(pdir) -> dict:
    """SHA-256 of every artifact the pilot analysis depends on, for a pilot directory."""
    pdir = Path(pdir)
    cfg = json.loads((pdir / CONFIG_FILE).read_text(encoding="utf-8"))
    packets = {str(p.relative_to(pdir)): sha256_file(p) for p in sorted((pdir / "packets").glob("*.md"))}
    return {
        "seed": cfg["seed"],
        "profile": {rel_to_repo(lift.PROFILE): sha256_file(lift.PROFILE)},
        "glossary": {rel_to_repo(lift.GLOSSARY): sha256_file(lift.GLOSSARY)},
        "scorer": {rel_to_repo(LIFT_DIR / "blind_experiment.py"): sha256_file(LIFT_DIR / "blind_experiment.py")},
        "pilot_scripts": {rel_to_repo(p): sha256_file(p) for p in pilot_script_paths()},
        "pilot_config": {CONFIG_FILE: sha256_file(pdir / CONFIG_FILE)},
        "allocation": {ALLOCATION_FILE: sha256_file(pdir / ALLOCATION_FILE)},
        "packets": packets,
    }


FREEZE_SECTIONS = ("seed", "profile", "glossary", "scorer", "pilot_scripts", "pilot_config", "allocation", "packets")


def verify_freeze(pdir):
    """Return a list of human-readable mismatches between pilot_freeze.json and the files now on disk."""
    pdir = Path(pdir)
    fz_path = pdir / FREEZE_FILE
    if not fz_path.is_file():
        return [f"{FREEZE_FILE} not found: run freeze.py before collecting any response"]
    fz = json.loads(fz_path.read_text(encoding="utf-8"))
    now = compute_freeze(pdir)
    problems = []
    for sec in FREEZE_SECTIONS:
        a, b = fz.get("hashes", {}).get(sec), now[sec]
        if isinstance(b, dict):
            a = a or {}
            for k in sorted(set(a) | set(b)):
                if a.get(k) != b.get(k):
                    problems.append(f"{sec}:{k} frozen={a.get(k)} now={b.get(k)}")
        elif a != b:
            problems.append(f"{sec} frozen={a} now={b}")
    return problems


def bootstrap_ci(values, reps, seed, lo=0.025, hi=0.975):
    """Participant-level percentile bootstrap of the mean (no binomial assumption)."""
    n = len(values)
    if n == 0:
        return None
    rng = random.Random(seed)
    means = sorted(sum(rng.choices(values, k=n)) / n for _ in range(reps))
    return [means[int(math.floor(lo * reps))], means[min(reps - 1, int(math.ceil(hi * reps)) - 1)]]
