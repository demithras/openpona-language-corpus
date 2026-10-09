"""Smoke tests for tooling. Not a semantic experiment."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"blind_experiment.py"
spec=importlib.util.spec_from_file_location("lift_harness",SCRIPT)
lift=importlib.util.module_from_spec(spec)
spec.loader.exec_module(lift)

class LiftHarnessTests(unittest.TestCase):
    def setUp(self):
        self.profile=lift.load_profile()

    def test_canonical_matrix_42_unique_and_fixed(self):
        grid=lift.validate(self.profile)
        self.assertEqual(len(grid),42)
        self.assertEqual(grid[(5,3)],"pana")
        self.assertEqual(grid[(5,5)],"tenpo")
        self.assertEqual(grid[(4,4)],"sama")

    def test_drift_is_rejected(self):
        p=json.loads(json.dumps(self.profile))
        p["cells"][2]["token"]="open"
        with self.assertRaises(ValueError): lift.validate(p)

    def test_seed_reproducible_and_no_truth_table_in_public(self):
        p1,a1,g1=lift.make_materials(self.profile,'external',20261008)
        p2,a2,g2=lift.make_materials(self.profile,'external',20261008)
        self.assertEqual(lift.digest(p1),lift.digest(p2))
        self.assertEqual(lift.digest(a1),lift.digest(a2))
        self.assertEqual(lift.digest(g1),lift.digest(g2))
        self.assertEqual(len(p1['trials']),42)
        self.assertEqual(len(p1['candidate_tokens']),42)
        self.assertNotIn('gold',p1)
        self.assertNotIn('token',p1['trials'][0])

    def test_primary_and_edge_size(self):
        pub,answers,gold=lift.make_materials(self.profile,'external',42)
        self.assertEqual(sum(x['is_primary_interior'] for x in pub['trials']),30)
        self.assertEqual(len(pub['trials'])-30,12)
        report=lift.score(gold,answers)
        self.assertEqual(report['totals']['interior']['n'],30)
        self.assertEqual(report['totals']['edge']['n'],12)
        self.assertEqual(report['totals']['all']['correct'],0)

    def test_perfect_answer_score_and_null_reproducible(self):
        pub,submission,gold=lift.make_materials(self.profile,'external',101)
        for a in submission['answers']: a['token']=gold['gold'][a['trial_id']]
        report=lift.score(gold,submission)
        self.assertEqual(report['totals']['interior']['correct'],30)
        self.assertEqual(report['totals']['edge']['correct'],12)
        one=lift.label_permutation_null(gold,submission,100,123)
        two=lift.label_permutation_null(gold,submission,100,123)
        self.assertEqual(one,two)
        self.assertAlmostEqual(one['p_ge_plus_one'],1/101,places=7)

    def test_missing_duplicate_invalid_answers(self):
        _,a,g=lift.make_materials(self.profile,'shuffled',7)
        bad=json.loads(json.dumps(a));bad['answers']=bad['answers'][:-1]
        with self.assertRaises(ValueError):lift.score(g,bad)
        bad=json.loads(json.dumps(a));bad['answers'][0]['token']='not-a-token'
        with self.assertRaises(ValueError):lift.score(g,bad)
        bad=json.loads(json.dumps(a));bad['answers'].append(bad['answers'][0])
        with self.assertRaises(ValueError):lift.score(g,bad)

    def test_control_conditions_are_distinct(self):
        ps={k:lift.make_materials(self.profile,k,5)[0] for k in lift.CONDITIONS}
        labels={k:(tuple(p['row_labels']),tuple(p['column_labels'])) for k,p in ps.items()}
        self.assertEqual(len(set(labels.values())),4)


def clone(p): return json.loads(json.dumps(p))

def cell(p, coord): return next(x for x in p["cells"] if x["coord"] == coord)

def drift_duplicate_token(p):
    cell(p, "R1C2")["token"] = cell(p, "R1C1")["token"]

def drift_row_five_swap(p):  # old historical variant: tenpo/pana exchanged
    a, b = cell(p, "R5C3"), cell(p, "R5C5")
    a["token"], b["token"] = b["token"], a["token"]

def drift_missing_slot(p):
    p["cells"] = [x for x in p["cells"] if x["coord"] != "R3C4"]

def drift_structural(p):
    a, b = cell(p, "R1C7"), cell(p, "R2C7")
    a["token"], b["token"] = b["token"], a["token"]

DRIFTS = {
    "duplicate_token": drift_duplicate_token,
    "row_five_drift": drift_row_five_swap,
    "missing_slot": drift_missing_slot,
    "structural_column_drift": drift_structural,
}


class DriftTests(unittest.TestCase):
    def test_current_profile_matches_repo_matrix(self):
        grid = lift.validate(lift.load_profile(), lift.load_matrix())
        self.assertEqual(grid, lift.load_matrix())

    def test_each_drift_kind_rejected_with_named_reason(self):
        for kind, mutate in DRIFTS.items():
            with self.subTest(kind=kind):
                p = clone(lift.load_profile()); mutate(p)
                with self.assertRaises(lift.DriftError) as cm:
                    lift.validate(p)
                self.assertEqual(cm.exception.kind, kind)

    def test_cli_exits_nonzero_with_reason_for_each_drift(self):
        for kind, mutate in DRIFTS.items():
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as d:
                p = clone(lift.load_profile()); mutate(p)
                f = Path(d) / "drifted.json"; f.write_text(json.dumps(p), encoding="utf-8")
                r = subprocess.run([sys.executable, str(SCRIPT), "validate", str(f)], capture_output=True, text=True)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(kind, r.stderr)

    def test_cli_validate_passes_on_frozen_profile(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "validate"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_token_not_in_repo_matrix_rejected(self):
        p = clone(lift.load_profile()); cell(p, "R6C6")["token"] = "pona2"
        with self.assertRaises(lift.DriftError) as cm:
            lift.validate(p)
        self.assertEqual(cm.exception.kind, "matrix_token_mismatch")


class PrepareDeterminismTests(unittest.TestCase):
    def test_prepare_twice_byte_identical_all_conditions(self):
        for cond in lift.CONDITIONS:
            with self.subTest(cond=cond), tempfile.TemporaryDirectory() as d:
                outs = []
                for tag in "ab":
                    pub, priv = Path(d) / tag / cond / "public", Path(d) / tag / cond / "private"
                    self.assertEqual(lift.main(["prepare", "--condition", cond, "--seed", "20261008", "--public-dir", str(pub), "--private-dir", str(priv)]), 0)
                    outs.append((pub, priv))
                self.assertEqual(sorted(x.name for x in outs[0][0].iterdir()), ["public_prompt.json", "submission_template.json"])
                self.assertEqual(sorted(x.name for x in outs[0][1].iterdir()), ["private_gold.json"])
                for i in (0, 1):
                    for n in sorted(x.name for x in outs[0][i].iterdir()):
                        self.assertEqual((outs[0][i] / n).read_bytes(), (outs[1][i] / n).read_bytes())


class PublicPrivateSeparationTests(unittest.TestCase):
    def run_prepare(self, pub, priv):
        return subprocess.run([sys.executable, str(SCRIPT), "prepare", "--condition", "external", "--seed", "1",
                               "--public-dir", str(pub), "--private-dir", str(priv)], capture_output=True, text=True)

    def test_equal_dirs_refused(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_prepare(Path(d) / "x", Path(d) / "x")
            self.assertNotEqual(r.returncode, 0)
            self.assertFalse((Path(d) / "x").exists())

    def test_nested_dirs_refused_both_ways(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotEqual(self.run_prepare(Path(d) / "x", Path(d) / "x" / "private").returncode, 0)
            self.assertNotEqual(self.run_prepare(Path(d) / "y" / "public", Path(d) / "y").returncode, 0)
            self.assertNotEqual(self.run_prepare(Path(d) / "z", Path(d) / "z" / ".." / "z").returncode, 0)

    def test_out_dir_flag_is_gone_and_both_dirs_required(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(SCRIPT), "prepare", "--condition", "external", "--seed", "1", "--out-dir", d + "/o"], capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)

    def test_gold_only_in_private_dir(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_prepare(Path(d) / "pub", Path(d) / "priv")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(d) / "priv" / "private_gold.json").is_file())
            for f in (Path(d) / "pub").iterdir():
                self.assertNotIn("private_gold", f.read_text(encoding="utf-8"))
                self.assertNotIn("gold", json.loads(f.read_text(encoding="utf-8")))

    def test_public_prompt_carries_identical_glossary_in_every_arm(self):
        gl = [lift.make_materials(lift.load_profile(), c, 5)[0]["glossary"] for c in lift.CONDITIONS]
        self.assertTrue(all(g == gl[0] for g in gl))
        self.assertEqual(set(gl[0]), set(lift.validate(lift.load_profile()).values()))


class GlossaryTests(unittest.TestCase):
    def setUp(self):
        self.g = json.loads(lift.GLOSSARY.read_text(encoding="utf-8"))

    def test_exactly_the_42_matrix_tokens(self):
        want = set(lift.load_matrix().values())
        have = set(self.g["definitions"])
        self.assertEqual(want - have, set())
        self.assertEqual(have - want, set())
        self.assertEqual(len(have), 42)

    def test_provenance_recorded(self):
        self.assertEqual(self.g["license"], "CC BY-SA 4.0")
        self.assertEqual(self.g["retrieved"], "2026-10-09")
        self.assertEqual(self.g["source_snapshot_sha256"], "369cc79d9b764feabcda59112d92171d486456be973b62fc6689a7442718e9d1")
        self.assertIn("lipu-linku/sona", self.g["source"])
        self.assertTrue((lift.GLOSSARY.parent / "LICENSE-NOTICE.md").is_file())
        self.assertTrue(all(isinstance(v, str) and v.strip() for v in self.g["definitions"].values()))

    def test_glossary_token_drift_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            bad = json.loads(json.dumps(self.g)); bad["definitions"].pop("open"); bad["definitions"]["pona2"] = "x"
            f = Path(d) / "g.json"; f.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(lift.DriftError) as cm:
                lift.load_glossary(lift.load_matrix(), f)
            self.assertEqual(cm.exception.kind, "glossary_token_mismatch")


def walk_pairs(node, trial_ids, token, found, path=""):
    """Collect places where a trial id is mapped (same object / key->value) to a token."""
    if isinstance(node, dict):
        ids = [v for v in node.values() if isinstance(v, str) and v in trial_ids]
        ids += [k for k in node if k in trial_ids]
        vals = [v for v in node.values() if isinstance(v, str)]
        for i in ids:
            for t in vals:
                found.append((i, t, path))
        for k, v in node.items():
            if k in trial_ids and isinstance(v, str):
                found.append((k, v, path))
            walk_pairs(v, trial_ids, token, found, path + "/" + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk_pairs(v, trial_ids, token, found, path + f"[{i}]")


class NoGoldLeakTests(unittest.TestCase):
    def test_no_gold_pair_in_public_files(self):
        for cond in lift.CONDITIONS:
            with self.subTest(cond=cond):
                pub, sub, gold = lift.make_materials(lift.load_profile(), cond, 20261008)
                g = gold["gold"]
                for name, doc in (("public_prompt", pub), ("submission_template", sub)):
                    found = []
                    walk_pairs(doc, set(g), None, found)
                    hits = [(i, t, p) for (i, t, p) in found if g[i] == t]
                    self.assertEqual(hits, [], f"{cond}/{name} leaks gold pairs")
                    self.assertNotIn("gold", doc)
                    self.assertNotIn("private_gold", json.dumps(doc))


class ScoreRejectionTests(unittest.TestCase):
    def setUp(self):
        _, self.sub, self.gold = lift.make_materials(lift.load_profile(), "external", 3)

    def test_missing_trial_rejected(self):
        bad = clone(self.sub); bad["answers"].pop()
        with self.assertRaisesRegex(ValueError, "missing trials"): lift.score(self.gold, bad)

    def test_duplicate_trial_rejected(self):
        bad = clone(self.sub); bad["answers"].append(clone(bad["answers"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate trial"): lift.score(self.gold, bad)

    def test_foreign_trial_rejected(self):
        bad = clone(self.sub); bad["answers"][0]["trial_id"] = "R9C9"
        with self.assertRaisesRegex(ValueError, "unknown trial"): lift.score(self.gold, bad)

    def test_foreign_metadata_rejected(self):
        bad = clone(self.sub); bad["condition"] = "generic"
        with self.assertRaises(ValueError): lift.score(self.gold, bad)


if __name__=='__main__':unittest.main()
