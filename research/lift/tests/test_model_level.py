import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
import model_level as ml  # noqa: E402

SECS = ("interior", "edge", "all", "interior_no_c7", "c7_interior")


def person(vendor, cond, v):
    return {"participant_id": f"{vendor}-{cond}-{v}", "vendor": vendor, "condition": cond,
            **{f"{s}_top1": v for s in SECS}}


def results(ext_minus_gen):
    """Synthetic results.json following analyze.py's schema ('participants' list)."""
    ps = []
    for vendor, d in ext_minus_gen.items():
        for cond, base in (("external", 0.5 + d), ("generic", 0.5), ("embedded", 0.5), ("shuffled", 0.5)):
            for i in range(3):
                ps.append(person(vendor, cond, base + (i - 1) * 0.1))
    return {"participants": ps}


class ModelLevelTest(unittest.TestCase):
    def test_all_three_agree(self):
        o = ml.analyse(results({"a": 0.2, "b": 0.2, "c": 0.2}), reps=200)
        c = o["contrasts"]["external_minus_generic_interior_no_c7"]
        self.assertEqual((c["k_positive"], c["M"]), (3, 3))
        self.assertAlmostEqual(c["sign_test_p_one_sided"], 0.125)
        self.assertAlmostEqual(c["mean_contrast"], 0.2)

    def test_one_reversed(self):
        o = ml.analyse(results({"a": 0.2, "b": 0.2, "c": -0.2}), reps=200)
        c = o["contrasts"]["external_minus_generic_interior_no_c7"]
        self.assertEqual((c["k_positive"], c["k_negative"], c["M"]), (2, 1, 3))
        self.assertAlmostEqual(c["sign_test_p_one_sided"], 0.5)

    def test_run_means(self):
        rs = {"participants": [person("a", "external", x) for x in (0.1, 0.2, 0.3)]
              + [person("a", "generic", 0.0)]}
        o = ml.analyse(rs, reps=50)
        s = o["per_model_arm"]["interior_no_c7"]["a"]["external"]
        self.assertAlmostEqual(s["mean"], 0.2)
        self.assertEqual(s["n_runs"], 3)

    def test_small_m_note_and_outputs(self):
        with tempfile.TemporaryDirectory() as t:
            r = Path(t) / "results.json"
            r.write_text(json.dumps(results({"a": 0.2, "b": 0.2, "c": 0.2})))
            self.assertEqual(ml.main(["--results", str(r), "--out-dir", t + "/out", "--seed", "1"]), 0)
            j = json.loads((Path(t) / "out" / "model_level.json").read_text())
            md = (Path(t) / "out" / "model_level.md").read_text()
        self.assertTrue(any("not interpretable as a population CI" in n
                            for n in j["contrasts"]["external_minus_generic_interior_no_c7"]["notes"]))
        self.assertTrue(md.startswith("# PILOT - EXPLORATORY, NOT CONFIRMATORY - unit of analysis: model (runs are not independent)"))
        self.assertIn("0.125", md)


if __name__ == "__main__":
    unittest.main()
