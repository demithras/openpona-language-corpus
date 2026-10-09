"""Tests for the Lift pilot operator kit (research/lift/pilot). Software behaviour only, no empirical claim."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

PILOT = Path(__file__).resolve().parents[1] / "pilot"
sys.path.insert(0, str(PILOT))
import pilotlib as pl  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location("pilot_" + name, PILOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


make_packets, freeze, ingest, analyze = (_load(n) for n in ("make_packets", "freeze", "ingest", "analyze"))
lift = pl.lift
GRID = lift.validate(lift.load_profile())
GOLD = {f"R{r}C{c}": t for (r, c), t in GRID.items()}
PAIR_WINDOW = 80


def run(mod, argv):
    """Run a script main() quietly; return (exit code, stderr text)."""
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
        code = mod.main(argv)
    return code, err.getvalue()


def leaked_pairs(text):
    """Gold (trial_id, token) pairs whose trial id and token appear within PAIR_WINDOW chars, or on one line."""
    hits = []
    for tid, tok in GOLD.items():
        ids = [m.start() for m in re.finditer(rf"\b{tid}\b", text)]
        toks = [m.start() for m in re.finditer(rf"(?<![\w.]){re.escape(tok)}(?![\w.])", text)]
        if any(abs(i - t) < PAIR_WINDOW for i in ids for t in toks):
            hits.append((tid, tok))
    return hits


def new_pilot(root, vendors="a", k=1, seed=1):
    d = Path(root) / "pilot"
    code, err = run(make_packets, ["--vendors", vendors, "--per-arm-per-vendor", str(k), "--seed", str(seed), "--out-dir", str(d)])
    assert code == 0, err
    return d


def write_private_gold(root):
    priv = Path(root) / "private"
    _, _, gold = lift.make_materials(lift.load_profile(), "external", 99)
    lift.dump_json(priv / "private_gold.json", gold)
    return priv


def reply(answers, familiarity="FAMILIARITY: no - never seen it."):
    body = json.dumps({"answers": [{"trial_id": k, "token": v} for k, v in answers.items()]})
    return f"Here is my answer.\n```json\n{body}\n```\n{familiarity}\n"


def packet_trial_ids(d, pid):
    return re.findall(r'"trial_id": "(R\dC\d)"', (Path(d) / "packets" / f"{pid}.md").read_text(encoding="utf-8"))


def respond(d, pid, answers, **kw):
    (Path(d) / "responses" / f"{pid}.txt").write_text(reply(answers, **kw), encoding="utf-8")


def arm_of(d, cond):
    return next(r["participant_id"] for r in pl.read_allocation(d) if r["condition"] == cond)


class PacketTests(unittest.TestCase):
    def test_no_gold_pair_in_any_packet_or_public_file(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root, vendors="a,b", k=2)
            packets = sorted((d / "packets").glob("*.md"))
            self.assertEqual(len(packets), 16)
            for p in packets:
                self.assertEqual(leaked_pairs(p.read_text(encoding="utf-8")), [], p.name)
            for cond in lift.CONDITIONS:
                pub = lift.make_materials(lift.load_profile(), cond, 1)[0]
                self.assertEqual(leaked_pairs(json.dumps(pub, indent=1)), [], cond)

    def test_leak_detector_catches_a_planted_pair(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root)
            text = next((d / "packets").glob("*.md")).read_text(encoding="utf-8") + f"\nR3C5 = {GOLD['R3C5']}\n"
            self.assertIn(("R3C5", GOLD["R3C5"]), leaked_pairs(text))

    def test_packet_contents(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root)
            for r in pl.read_allocation(d):
                t = (d / r["packet"]).read_text(encoding="utf-8")
                self.assertEqual(sorted(packet_trial_ids(d, r["participant_id"])), sorted(GOLD))
                self.assertIn(pl.FAMILIARITY_QUESTION, t)
                self.assertGreater(t.index(pl.FAMILIARITY_QUESTION), t.index('"answers"'))
                for tok, definition in lift.load_glossary(GRID).items():
                    self.assertIn(f"- {tok}: {definition}", t)
                self.assertNotIn(r["condition"] + " arm", t)

    def test_glossary_identical_across_arms_but_labels_differ(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root)
            gl, labels = set(), set()
            for r in pl.read_allocation(d):
                t = (d / r["packet"]).read_text(encoding="utf-8")
                gl.add(tuple(sorted(l for l in t.splitlines() if re.match(r"- [a-z]+: ", l) and not l.startswith("- Row") and not l.startswith("- Column"))))
                labels.add(t[t.index("## Row labels"):t.index("## Candidate tokens")])
            self.assertEqual(len(gl), 1)
            self.assertEqual(len(labels), 4)

    def test_deterministic_per_seed(self):
        with tempfile.TemporaryDirectory() as r1, tempfile.TemporaryDirectory() as r2, tempfile.TemporaryDirectory() as r3:
            a, b, c = new_pilot(r1, "a,b", 2, 5), new_pilot(r2, "a,b", 2, 5), new_pilot(r3, "a,b", 2, 6)
            files = sorted(str(p.relative_to(a)) for p in a.rglob("*") if p.is_file())
            self.assertEqual(files, sorted(str(p.relative_to(b)) for p in b.rglob("*") if p.is_file()))
            for f in files:
                self.assertEqual((a / f).read_bytes(), (b / f).read_bytes(), f)
            self.assertNotEqual((a / "allocation.csv").read_bytes(), (c / "allocation.csv").read_bytes())

    def test_counterbalanced_orders_and_allocation(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root, "a,b", 2)
            rows = pl.read_allocation(d)
            cells = {}
            for r in rows:
                cells.setdefault((r["vendor"], r["condition"]), []).append(r)
            self.assertEqual(len(cells), 8)
            for key, rs in cells.items():
                self.assertEqual(len(rs), 2, key)
                o = []
                for r in sorted(rs, key=lambda x: x["cell_index"]):
                    t = (d / r["packet"]).read_text(encoding="utf-8")
                    o.append(re.findall(r"^- ([a-z]+): ", t[t.index("## Candidate"):t.index("## Trials")], re.M))
                self.assertEqual(o[0], o[1][::-1], key)
        # candidate order must not equal the matrix reading order
        self.assertNotEqual(o[0], [GRID[(r, c)] for r in range(1, 7) for c in range(1, 8)])

    def test_bad_arguments_and_nonempty_out_dir_refused(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root)
            code, _ = run(make_packets, ["--vendors", "a", "--seed", "1", "--out-dir", str(d)])
            self.assertEqual(code, 2)
            code, _ = run(make_packets, ["--vendors", "a,a", "--seed", "1", "--out-dir", str(Path(root) / "q")])
            self.assertEqual(code, 2)


class FreezeTests(unittest.TestCase):
    def test_freeze_detects_one_byte_change_in_a_packet(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root)
            self.assertEqual(run(freeze, ["--dir", str(d)])[0], 0)
            fz = json.loads((d / pl.FREEZE_FILE).read_text(encoding="utf-8"))["hashes"]
            for key in ("profile", "glossary", "scorer", "pilot_scripts", "packets", "allocation", "seed"):
                self.assertIn(key, fz)
            self.assertEqual(len(fz["packets"]), 4)
            self.assertEqual(pl.verify_freeze(d), [])
            p = next((d / "packets").glob("*.md"))
            raw = bytearray(p.read_bytes()); raw[100] ^= 1; p.write_bytes(bytes(raw))
            problems = pl.verify_freeze(d)
            self.assertEqual(len(problems), 1)
            self.assertIn(f"packets:packets/{p.name}", problems[0])
            self.assertEqual(run(freeze, ["--dir", str(d), "--check"])[0], 3)
            self.assertEqual(run(ingest, ["--dir", str(d)])[0], 2)

    def test_freeze_refuses_after_a_response_and_when_already_frozen(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root)
            (d / "responses" / "p001.txt").write_text("x", encoding="utf-8")
            code, err = run(freeze, ["--dir", str(d)])
            self.assertEqual(code, 2); self.assertIn("precede every response", err)
            (d / "responses" / "p001.txt").unlink()
            self.assertEqual(run(freeze, ["--dir", str(d)])[0], 0)
            self.assertEqual(run(freeze, ["--dir", str(d)])[0], 2)

    def test_changed_allocation_or_script_hash_is_detected(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root)
            run(freeze, ["--dir", str(d)])
            fzp = d / pl.FREEZE_FILE
            fz = json.loads(fzp.read_text(encoding="utf-8"))
            fz["hashes"]["pilot_scripts"][next(iter(fz["hashes"]["pilot_scripts"]))] = "0" * 64
            fz["hashes"]["seed"] = 2
            fzp.write_text(json.dumps(fz), encoding="utf-8")
            self.assertEqual(len(pl.verify_freeze(d)), 2)
            (d / "allocation.csv").write_text((d / "allocation.csv").read_text().replace("external", "generic", 1), encoding="utf-8")
            self.assertEqual(len(pl.verify_freeze(d)), 3)


class IngestTests(unittest.TestCase):
    def setUp(self):
        self._root = tempfile.TemporaryDirectory(); self.addCleanup(self._root.cleanup)
        self.d = new_pilot(self._root.name)
        run(freeze, ["--dir", str(self.d)])
        self.pid = pl.read_allocation(self.d)[0]["participant_id"]
        self.perfect = dict(GOLD)

    def ingest(self):
        code, err = run(ingest, ["--dir", str(self.d)])
        self.assertEqual(code, 0, err)
        return json.loads((self.d / "ingest_log.json").read_text(encoding="utf-8"))

    def excluded_reason(self):
        log = self.ingest()
        self.assertEqual(log["accepted"], [])
        return log["excluded"][0]["reason"]

    def test_extracts_json_from_surrounding_prose_and_records_familiarity(self):
        text = "Thinking out loud {not json} first.\n" + reply(self.perfect, "**FAMILIARITY:** unsure - the grid looks vaguely familiar") + "Thanks!"
        (self.d / "responses" / f"{self.pid}.txt").write_text(text, encoding="utf-8")
        log = self.ingest()
        self.assertEqual(log["accepted"], [self.pid])
        rec = json.loads((self.d / "parsed" / f"{self.pid}.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["familiarity_answer"], "unsure")
        self.assertEqual({a["trial_id"]: a["token"] for a in rec["answers"]}, GOLD)

    def test_accepts_abstention_and_bare_json_without_fence(self):
        ans = dict(GOLD); ans["R2C2"] = ""
        (self.d / "responses" / f"{self.pid}.txt").write_text(json.dumps({"answers": [{"trial_id": k, "token": v} for k, v in ans.items()]}), encoding="utf-8")
        log = self.ingest()
        self.assertEqual(log["accepted"], [self.pid])
        rec = json.loads((self.d / "parsed" / f"{self.pid}.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["familiarity_answer"], "missing")

    def test_rejects_missing_id(self):
        ans = dict(GOLD); ans.pop("R4C4")
        respond(self.d, self.pid, ans)
        self.assertEqual(self.excluded_reason(), "missing_trial_id")

    def test_rejects_duplicate_id(self):
        rows = [{"trial_id": k, "token": v} for k, v in GOLD.items()] + [{"trial_id": "R1C1", "token": "open"}]
        (self.d / "responses" / f"{self.pid}.txt").write_text(json.dumps({"answers": rows}), encoding="utf-8")
        self.assertEqual(self.excluded_reason(), "duplicate_trial_id")

    def test_rejects_foreign_id_and_foreign_token(self):
        ans = dict(GOLD); ans["R9C9"] = ans.pop("R1C1")
        respond(self.d, self.pid, ans)
        self.assertEqual(self.excluded_reason(), "foreign_trial_id")
        ans = dict(GOLD); ans["R1C1"] = "Open"
        respond(self.d, self.pid, ans)
        self.assertEqual(self.excluded_reason(), "foreign_token")

    def test_rejects_no_json_and_ambiguous_replies_and_unknown_participant(self):
        (self.d / "responses" / f"{self.pid}.txt").write_text("I refuse.", encoding="utf-8")
        self.assertEqual(self.excluded_reason(), "no_json_answer_object")
        blank = {k: "" for k in GOLD}
        (self.d / "responses" / f"{self.pid}.txt").write_text(reply(blank) + reply(self.perfect), encoding="utf-8")
        self.assertEqual(self.excluded_reason(), "multiple_distinct_answer_objects")
        (self.d / "responses" / f"{self.pid}.txt").unlink()
        (self.d / "responses" / "zzz.txt").write_text(reply(self.perfect), encoding="utf-8")
        self.assertEqual(self.excluded_reason(), "unknown_participant_id")

    def test_rejection_is_logged_not_silent_and_stale_parsed_removed(self):
        respond(self.d, self.pid, self.perfect)
        self.assertEqual(self.ingest()["accepted"], [self.pid])
        ans = dict(GOLD); ans.pop("R4C4"); respond(self.d, self.pid, ans)
        log = self.ingest()
        self.assertEqual(log["excluded"][0]["participant_id"], self.pid)
        self.assertEqual(list((self.d / "parsed").glob("*.json")), [])
        self.assertEqual(len(log["allocated_without_response"]), 3)


class AnalyzeTests(unittest.TestCase):
    def setUp(self):
        self._root = tempfile.TemporaryDirectory(); self.addCleanup(self._root.cleanup)
        self.d = new_pilot(self._root.name)
        self.priv = write_private_gold(self._root.name)
        run(freeze, ["--dir", str(self.d)])

    def analyse(self, **kw):
        code, err = run(ingest, ["--dir", str(self.d)])
        self.assertEqual(code, 0, err)
        code, err = run(analyze, ["--dir", str(self.d), "--gold", str(self.priv), "--boot-reps", "200", "--null-reps", "200"])
        self.assertEqual(code, kw.get("code", 0), err)
        return json.loads((self.d / "results.json").read_text(encoding="utf-8")) if code == 0 else None

    def person(self, res, pid):
        return next(p for p in res["participants"] if p["participant_id"] == pid)

    def test_perfect_gives_30_30_for_everyone(self):
        for r in pl.read_allocation(self.d):
            respond(self.d, r["participant_id"], GOLD)
        res = self.analyse()
        self.assertEqual(len(res["participants"]), 4)
        for p in res["participants"]:
            self.assertEqual((p["interior_correct"], p["edge_correct"], p["all_correct"]), (30, 12, 42))
        for arm in res["arms"].values():
            self.assertEqual(arm["interior"]["mean_top1"], 1.0)
            self.assertEqual(arm["interior"]["ci95_participant_bootstrap"], [1.0, 1.0])
        self.assertTrue((self.d / "report.md").read_text(encoding="utf-8").startswith("# PILOT - EXPLORATORY, NOT CONFIRMATORY"))
        self.assertEqual(next(iter(res)), "banner")
        self.assertEqual(res["banner"], "PILOT - EXPLORATORY, NOT CONFIRMATORY")

    def test_all_abstain_gives_zero(self):
        for r in pl.read_allocation(self.d):
            respond(self.d, r["participant_id"], {k: "" for k in GOLD})
        res = self.analyse()
        for p in res["participants"]:
            self.assertEqual((p["interior_correct"], p["edge_correct"], p["all_correct"], p["abstained"]), (0, 0, 0, 42))
        for arm in res["arms"].values():
            self.assertEqual(arm["interior"]["mean_top1"], 0.0)

    def test_hand_computed_partial_case(self):
        # Interior: R2C2..R2C7 (6) and R3C2..R3C4 (3) right = 9/30; R4C2 wrong token (R4C3's gold), R5C2 abstained.
        # Edge (row 1 or column 1): R1C1, R1C2, R6C1 right = 3/12; R1C3 wrong token. Everything else abstained. All = 12/42.
        part = {k: "" for k in GOLD}
        right = [f"R2C{c}" for c in range(2, 8)] + [f"R3C{c}" for c in range(2, 5)] + ["R1C1", "R1C2", "R6C1"]
        for k in right:
            part[k] = GOLD[k]
        part["R4C2"] = GOLD["R4C3"]
        part["R1C3"] = GOLD["R1C4"]
        pid_ext, pid_gen = arm_of(self.d, "external"), arm_of(self.d, "generic")
        respond(self.d, pid_ext, part)
        respond(self.d, pid_gen, GOLD)
        res = self.analyse()
        p = self.person(res, pid_ext)
        self.assertEqual((p["interior_correct"], p["edge_correct"], p["all_correct"]), (9, 3, 12))
        self.assertAlmostEqual(p["interior_top1"], 0.3)
        self.assertAlmostEqual(p["edge_top1"], 0.25)
        self.assertAlmostEqual(p["all_top1"], 12 / 42, places=7)
        self.assertEqual(p["abstained"], 42 - 12 - 2)
        conf = res["arms"]["external"]["per_cell_confusion"]
        self.assertEqual(conf["R4C2"]["answers"], {GOLD["R4C3"]: 1})
        self.assertEqual(conf["R4C2"]["correct"], 0)
        self.assertEqual(conf["R2C2"]["correct"], 1)
        self.assertEqual(conf["R5C2"]["answers"], {"": 1})
        self.assertEqual(res["arms"]["external"]["interior"]["mean_top1"], p["interior_top1"])
        self.assertAlmostEqual(res["contrasts"]["external_minus_generic_interior"]["difference_of_means"], 0.3 - 1.0)
        self.assertEqual(res["allocated_without_response"].__len__(), 2)

    def test_two_participants_in_one_arm_average(self):
        with tempfile.TemporaryDirectory() as root:
            d = new_pilot(root, vendors="a,b", k=1)
            priv = write_private_gold(root)
            run(freeze, ["--dir", str(d)])
            ext = [r["participant_id"] for r in pl.read_allocation(d) if r["condition"] == "external"]
            half = {k: (v if k.startswith("R2") else "") for k, v in GOLD.items()}  # R2C2..R2C7 = 6 interior
            respond(d, ext[0], GOLD); respond(d, ext[1], half)
            self.assertEqual(run(ingest, ["--dir", str(d)])[0], 0)
            self.assertEqual(run(analyze, ["--dir", str(d), "--gold", str(priv), "--boot-reps", "300", "--null-reps", "100"])[0], 0)
            res = json.loads((d / "results.json").read_text(encoding="utf-8"))
            arm = res["arms"]["external"]
            self.assertAlmostEqual(arm["interior"]["mean_top1"], (1.0 + 6 / 30) / 2)
            lo, hi = arm["interior"]["ci95_participant_bootstrap"]
            self.assertAlmostEqual(lo, 0.2); self.assertAlmostEqual(hi, 1.0)
            self.assertEqual(res["arms"]["external"]["n_participants"], 2)

    def test_analyze_refuses_when_freeze_hashes_changed(self):
        for r in pl.read_allocation(self.d):
            respond(self.d, r["participant_id"], GOLD)
        self.assertEqual(run(ingest, ["--dir", str(self.d)])[0], 0)
        p = next((self.d / "packets").glob("*.md"))
        p.write_text(p.read_text(encoding="utf-8") + " ", encoding="utf-8")
        code, err = run(analyze, ["--dir", str(self.d), "--gold", str(self.priv)])
        self.assertEqual(code, 2); self.assertIn("freeze", err)
        self.assertFalse((self.d / "results.json").exists())

    def test_analyze_refuses_wrong_gold_and_no_responses(self):
        code, err = run(analyze, ["--dir", str(self.d), "--gold", str(self.priv)])
        self.assertEqual(code, 2); self.assertIn("no parsed responses", err)
        bad = json.loads((self.priv / "private_gold.json").read_text(encoding="utf-8"))
        bad["gold"]["R2C2"], bad["gold"]["R2C3"] = bad["gold"]["R2C3"], bad["gold"]["R2C2"]
        lift.dump_json(self.priv / "private_gold.json", bad)
        respond(self.d, pl.read_allocation(self.d)[0]["participant_id"], GOLD)
        self.assertEqual(run(ingest, ["--dir", str(self.d)])[0], 0)
        code, err = run(analyze, ["--dir", str(self.d), "--gold", str(self.priv)])
        self.assertEqual(code, 2); self.assertIn("differs from data/matrix.csv", err)

    def test_pilot_dir_inside_gold_dir_is_not_required_and_gold_never_in_pilot_dir(self):
        self.assertEqual([p for p in self.d.rglob("*") if p.is_file() and "private_gold" in p.name], [])


if __name__ == "__main__":
    unittest.main()
