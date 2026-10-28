"""TP-04 corpus integrity: frozen baseline, unique ids, complete records, generated counts,
no silently skipped property tests, and the independence/triage of the oracle.

These checks fail CI on: a changed baseline file, a duplicate id, a record without
rationale/source rule/review, a stale hand-typed case count, a skip-on-missing-dependency in tests/,
a triage entry that names no case, an oracle that imports the parser or its grammar.
"""
from __future__ import annotations

import ast as pyast
import hashlib
import importlib
import importlib.util
import json
import re
import subprocess
import sys
import types
from pathlib import Path

import hypothesis  # noqa: F401  (hard import: a missing dependency is a collection error)
import pytest

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "conformance"
ORACLE_DIR = ROOT / "tools" / "oracle"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import conformance_counts as cc  # noqa: E402
from tools.oracle import recognizer as oracle  # noqa: E402

BASELINE_FILES = ["basic.jsonl", "grouping.jsonl", "invalid.jsonl", "meta.jsonl",
                  "tan_dual.jsonl", "toki_pona_compat.jsonl"]
REQUIRED_NEW = ("id", "surface", "rationale", "source_rule", "expect_status", "review")
REVIEW = "PROPOSED - PENDING AUTHOR REVIEW"
# Records the author accepted on 2026-10-09: every case of canon_2026_10_09.jsonl (D3-D5) and
# every case of ambiguity_v2.jsonl (the 36 proposed ones were accepted as a batch).  Nothing in
# any other file may be ACCEPTED.  An ACCEPTED record must cite that decision in source_rule.
ACCEPTED = "ACCEPTED - author decision 2026-10-09"
# 2026-10-28 (N2, phrase length by position): every case of canon_2026_10_28.jsonl is accepted and
# cites that decision; records of older files that N2 forced to change carry a `decision` field.
ACCEPTED_N2 = "ACCEPTED - author decision 2026-10-28"
N2_FILE = "canon_2026_10_28.jsonl"
REVIEWS = (REVIEW, ACCEPTED, ACCEPTED_N2)
DECIDED_FILES = ("canon_2026_10_09.jsonl", "ambiguity_v2.jsonl", N2_FILE)
DECISION_FILE = "canon_2026_10_09.jsonl"
RECORDS = cc.load_records()
TRIAGED = json.loads((ORACLE_DIR / "triaged.json").read_text(encoding="utf-8"))


def _canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _new_records():
    return [(f, n, r) for f, n, r in RECORDS if f not in BASELINE_FILES]


# --------------------------------------------------------------- frozen baseline
def _lock():
    out = {}
    for line in (CONF / "BASELINE.lock").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            digest, name = line.split(None, 1)
            out[name.strip()] = digest
    return out


def test_baseline_lock_lists_exactly_the_six_original_files():
    assert sorted(_lock()) == sorted(f"conformance/{n}" for n in BASELINE_FILES)


@pytest.mark.parametrize("name", BASELINE_FILES)
def test_baseline_file_is_byte_identical_to_its_lock(name):
    data = (CONF / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == _lock()[f"conformance/{name}"], (
        f"{name} changed: a baseline expectation needs an author decision record and a "
        "deliberate edit of conformance/BASELINE.lock")


def test_baseline_provenance_indexes_every_baseline_case_once():
    prov = json.loads((CONF / "baseline_provenance.json").read_text(encoding="utf-8"))
    base = [r for f, _n, r in RECORDS if f in BASELINE_FILES]
    assert sorted(prov["cases"]) == sorted(r["id"] for r in base)
    assert prov["baseline_case_count"] == len(base) == len(prov["cases"])
    for r in base:
        entry = prov["cases"][r["id"]]
        assert entry["expect_status"] == r["expect_status"] and entry["note"] == r.get("note", "")
        if re.search(r"decision", r.get("note", ""), re.I):
            assert entry["decision_refs"], r["id"]


# --------------------------------------------------------------- ids and fields
def test_no_duplicate_ids_across_all_conformance_files():
    assert cc.duplicate_ids() == []
    ids = [r["id"] for _f, _n, r in RECORDS]
    assert len(ids) == len(set(ids)) == len(RECORDS)


def test_the_duplicate_id_check_detects_a_duplicate(tmp_path):
    (tmp_path / "a.jsonl").write_text('{"id":"x1"}\n{"id":"x2"}\n', encoding="utf-8")
    (tmp_path / "b.jsonl").write_text('{"id":"x1"}\n', encoding="utf-8")
    assert cc.duplicate_ids(tmp_path) == ["x1"]


def test_at_least_twenty_new_ambiguity_cases():
    v2 = [r for f, _n, r in RECORDS if f == "ambiguity_v2.jsonl"]
    assert len(v2) >= 20
    assert all(r["id"].startswith("amb2-") for r in v2)


def test_every_new_record_has_all_required_fields_and_expected_trees():
    missing = {}
    for f, n, r in _new_records():
        gaps = [k for k in REQUIRED_NEW
                if not isinstance(r.get(k), str) or (k != "surface" and not r[k].strip())]
        if r["expect_status"] != "INVALID":
            if not r.get("expect_skeletons"):
                gaps.append("expect_skeletons")
            if not r.get("expect_asts") or len(r["expect_asts"]) != len(r.get("expect_skeletons", [])):
                gaps.append("expect_asts")
        if r.get("review") not in REVIEWS:
            gaps.append("review")
        if gaps:
            missing[r.get("id", f"{f}:{n}")] = gaps
    assert missing == {}


def test_new_expectations_are_proposals_unless_the_author_decided_them():
    for f, _n, r in _new_records():
        decided = f in DECIDED_FILES
        accepted = ACCEPTED_N2 if f == N2_FILE else ACCEPTED
        assert r["review"] == (accepted if decided else REVIEW), r["id"]
        if decided:
            assert accepted.split("- ")[1] in r["source_rule"], r["id"]
            assert "triage" not in r, r["id"]             # a decided case is never skipped
        assert r["expect_status"] in cc.STATUSES


def test_decision_cases_cover_d3_d4_d5_and_keep_their_edge_characters():
    recs = {r["id"]: r for f, _n, r in RECORDS if f == DECISION_FILE}
    surfaces = {r["surface"]: r["expect_status"] for r in recs.values()}
    assert {"jan pi jan jan", "jan pi ma ma", "jan pali li ma ma tan ma tan",
            "tan ni li jan jan tan jan tan"} <= set(surfaces)
    assert sum(1 for i in recs if i.startswith("canon-d4-")) >= 4
    # the line-edge characters survive the jsonl round trip (JSON escapes, ASCII file)
    assert surfaces == {**surfaces, "ilo pali li awen\n": "RESOLVED", "ilo pali li awen\r\n": "RESOLVED",
                        "ilo pali li awen\n\n": "INVALID", "\nilo pali li awen": "INVALID",
                        "ilo pali li awen\u2028": "INVALID", "ilo pali li awen\r": "INVALID",
                        "\tilo pali li awen\t": "RESOLVED"}
    for path in sorted(CONF.glob("*.jsonl")):
        text = path.read_text(encoding="utf-8")
        # one physical line per record: no raw line boundary inside a JSON string
        assert text.splitlines() == text.rstrip("\n").split("\n"), path.name


def test_expect_asts_are_span_free_n2_trees_whose_skeletons_match():
    ast_mod = importlib.import_module("openpona.ast")
    for _f, _n, r in _new_records():
        if r["expect_status"] == "INVALID":
            continue
        got = []
        for tree in r["expect_asts"]:
            assert "span" not in _canon(tree)
            assert tree["type"] in ast_mod.NODE_TYPES
            got.append(_canon(tree))
        # independent of the parser: the oracle's own trees for the same surface
        assert sorted(got) == sorted(_canon(s) for s in oracle.recognize(r["surface"]).shapes), r["id"]


# --------------------------------------------------------------- changed expectations
def test_changed_v2_expectations_need_a_decision_record():
    lock = json.loads((CONF / "ambiguity_v2.digests.json").read_text(encoding="utf-8"))
    problems = []
    for f, _n, r in RECORDS:
        if f != "ambiguity_v2.jsonl":
            continue
        digest = cc.expectation_digest(r)
        if r["id"] not in lock:
            problems.append((r["id"], "new record without a digest entry"))
        elif lock[r["id"]] != digest and not str(r.get("decision", "")).strip():
            problems.append((r["id"], "expectation changed without a `decision` field"))
    stale = sorted(set(lock) - {r["id"] for f, _n, r in RECORDS if f == "ambiguity_v2.jsonl"})
    assert problems == [] and stale == []


# --------------------------------------------------------------- counts are generated
def test_counts_are_generated_from_the_cases_and_the_cli_agrees():
    per_file, total = cc.count()
    assert sum(total.values()) == len(RECORDS)
    assert set(total) <= set(cc.STATUSES)
    by_hand = {s: sum(1 for _f, _n, r in RECORDS if r["expect_status"] == s) for s in cc.STATUSES}
    assert {s: total[s] for s in cc.STATUSES} == by_hand
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "conformance_counts.py"), "--json"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["all"] == len(RECORDS) and out["total"] == dict(total) and out["duplicate_ids"] == []
    assert set(out["files"]) == {f for f, _n, _r in RECORDS}
    text = subprocess.run([sys.executable, str(ROOT / "tools" / "conformance_counts.py")],
                          capture_output=True, text=True, timeout=60).stdout
    assert re.search(rf"TOTAL\s+{total['RESOLVED']}\s+{total['INVALID']}\s+{total['AMBIGUOUS']}\s+{len(RECORDS)}", text)


CURRENT_STATE_DOCS = ["MANIFEST.json", "README.md", "AGENTS.md", "CHEATSHEET.md", "CONTRIBUTING.md",
                      "conformance/README.md", "docs/parser-api.md", "docs/parser-complexity.md",
                      "docs/record-profiles.md", "docs/for-agents.md"]
COUNT_TEXT = re.compile(
    r"(?:conformance\s+corpus[:\s]+(\d+)\s+cases?)|(?:\b(\d+)\s+(?:conformance\s+)?(?:cases|records)\b"
    r"(?=[^.\n]*\b(?:total|in all|in the corpus)\b))|(?:\b(\d+)\s+conformance\s+cases?\b)", re.I)


def test_no_hand_typed_case_count_in_current_state_docs_is_stale():
    total = len(RECORDS)
    stale = []
    for rel in CURRENT_STATE_DOCS:
        path = ROOT / rel
        if not path.exists():
            continue
        for m in COUNT_TEXT.finditer(path.read_text(encoding="utf-8")):
            n = int(next(g for g in m.groups() if g))
            if n != total:
                stale.append((rel, m.group(0)))
    assert stale == [], f"stale count text (generate it: tools/conformance_counts.py): {stale}"


def test_the_stale_count_check_recognises_a_stale_phrase():
    assert COUNT_TEXT.search("conformance corpus 81 cases")
    assert COUNT_TEXT.search("The 96 conformance cases give")
    assert not COUNT_TEXT.search("The 96 baseline conformance cases give")


# --------------------------------------------------------------- Hypothesis is mandatory
def test_no_test_may_skip_a_missing_dependency_silently():
    needle = "import" + "orskip"
    offenders = [p.name for p in sorted((ROOT / "tests").glob("*.py"))
                 if needle in p.read_text(encoding="utf-8")]
    assert offenders == []


def test_hypothesis_is_a_declared_test_dependency():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'test\s*=\s*\[[^\]]*"hypothesis', pyproject)


# --------------------------------------------------------------- triage
def test_every_open_triage_record_is_listed_in_the_oracle_triage_and_vice_versa():
    open_ids = {r["id"] for _f, _n, r in RECORDS if r.get("triage") == "open"}
    listed = {k for k in TRIAGED if not k.startswith("_")}
    all_ids = {r["id"] for _f, _n, r in RECORDS}
    assert listed <= all_ids
    assert open_ids <= listed
    for _f, _n, r in RECORDS:
        if r.get("triage") == "open":
            assert r.get("triage_note", "").strip(), r["id"]
            assert "PENDING AUTHOR" in r["triage_note"]
    for k in listed:
        assert TRIAGED[k]["class"] and TRIAGED[k]["note"]


# --------------------------------------------------------------- the oracle itself
def test_oracle_has_no_import_path_to_the_parser_or_its_grammar():
    forbidden = re.compile(r"import lark|from lark|import openpona|from openpona|grammar\.lark")
    for path in sorted(ORACLE_DIR.glob("*.py")):
        assert not forbidden.search(path.read_text(encoding="utf-8")) or path.name == "compare.py", path
    tree = pyast.parse((ORACLE_DIR / "recognizer.py").read_text(encoding="utf-8"))
    roots = set()
    for node in pyast.walk(tree):
        if isinstance(node, pyast.Import):
            roots |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, pyast.ImportFrom):
            roots.add((node.module or "").split(".")[0])
    assert roots <= {"__future__", "csv", "re", "dataclasses", "functools", "pathlib"}, roots
    # nothing in tools/oracle imports the parser statically, the driver included
    for path in sorted(ORACLE_DIR.glob("*.py")):
        for node in pyast.walk(pyast.parse(path.read_text(encoding="utf-8"))):
            mods = ([a.name for a in node.names] if isinstance(node, pyast.Import)
                    else [node.module or ""] if isinstance(node, pyast.ImportFrom) else [])
            assert not any(m.split(".")[0] in ("openpona", "lark") for m in mods), (path, mods)


def test_oracle_matches_every_untriaged_expectation_in_the_corpus():
    bad = []
    for _f, _n, r in RECORDS:
        if r.get("triage") == "open":
            continue
        o = oracle.recognize(r["surface"])
        want = sorted(set(r.get("expect_skeletons", [])))
        if o.status != r["expect_status"] or (r["expect_status"] != "INVALID" and o.skeletons != want):
            bad.append(r["id"])
    assert bad == []


def test_oracle_rejects_the_whole_must_reject_set_and_accepts_positive_controls():
    for _f, _n, r in RECORDS:
        if _f == "toki_pona_compat.jsonl":
            assert oracle.recognize(r["surface"]).status == "INVALID", r["id"]
    for s in ("nasin open anu nasin awen li pali", "tan toki ni la jan pali li pali", "jan jan li pali"):
        assert oracle.recognize(s).status == "RESOLVED"


def test_oracle_known_negatives_do_not_match_everything():
    # a checker that says INVALID (or RESOLVED) for everything would also pass half the corpus
    verdicts = {oracle.recognize(r["surface"]).status for _f, _n, r in RECORDS}
    assert verdicts == {"RESOLVED", "INVALID", "AMBIGUOUS"}
    assert oracle.recognize("sona pi lawa").status == "INVALID"
    assert oracle.recognize("jan pali jan pali jan").skeletons == [
        "{D1(jan pali) jan}", "{jan D1(pali jan)}"]


def _load_compare():
    spec = importlib.util.spec_from_file_location("oracle_compare", ORACLE_DIR / "compare.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_compare_driver_exits_zero_with_no_disagreement(tmp_path):
    # since the author decisions of 2026-10-09 the oracle and the parser agree on every case
    report = tmp_path / "disagreements.md"
    proc = subprocess.run([sys.executable, str(ORACLE_DIR / "compare.py"), "--report", str(report)],
                          capture_output=True, text=True, timeout=300, cwd=ROOT)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = report.read_text(encoding="utf-8")
    assert f"- agree (status, skeleton set and span-free AST shape): {len(RECORDS)}" in text
    assert "- disagree: 0;" in text and "NOT triaged: 0" in text
    assert [k for k in TRIAGED if not k.startswith("_")] == []


def test_compare_driver_fails_on_an_untriaged_disagreement_and_on_a_stale_entry(tmp_path, capsys):
    compare = _load_compare()
    wrong_parser = types.SimpleNamespace(parse=lambda s: types.SimpleNamespace(
        status="INVALID", skeletons=[], alternatives=()))
    ast_mod = importlib.import_module("openpona.ast")
    ok, kind, _o, _p = compare.compare_case({"surface": "jan pali li pali"}, wrong_parser, ast_mod)
    assert (ok, kind) == (False, "status")
    # a triage entry for a case that no longer disagrees is stale: exit 1
    stale = tmp_path / "t.json"
    stale.write_text('{"amb2-meta-09": {"class": "x", "note": "y"}}', encoding="utf-8")
    proc = subprocess.run([sys.executable, str(ORACLE_DIR / "compare.py"), "--report",
                           str(tmp_path / "r.md"), "--triaged", str(stale)],
                          capture_output=True, text=True, timeout=300, cwd=ROOT)
    assert proc.returncode == 1 and "stale=['amb2-meta-09']" in proc.stdout
    # an untriaged disagreement: exit 1 and named (the driver loads the parser by name)
    real_import = compare.importlib.import_module
    compare.importlib = types.SimpleNamespace(import_module=lambda name: wrong_parser
                                              if name == "openpona" else real_import(name))
    empty = tmp_path / "e.json"
    empty.write_text("{}", encoding="utf-8")
    try:
        code = compare.main(["--report", str(tmp_path / "w.md"), "--triaged", str(empty)])
    finally:
        compare.importlib = importlib
    assert code == 1
    assert "UNTRIAGED amb2-meta-09" in capsys.readouterr().out


# --------------------------------------------------------------- N2 (phrase length by position)
# Author decision 2026-10-28: a phrase of exactly one surface token is allowed only in PREDICATE
# position (main expression after li; a bare statement).  Every nominal phrase (subject, object,
# source, context, each anu alternative there) needs >= 2 surface tokens.  This checker reads the
# expected SKELETONS of the corpus (conformance/README.md notation); it does not touch the parser
# or the oracle, so it also guards the expectations themselves.
_SKEL = re.compile(r"\{[^}]*\}|\(|\)|[a-z]+")


def _phrase_tokens(body):
    if re.search(r"\bpi\b", body):
        return 99                                  # a pi group always gives >= 3 tokens
    return sum((int(m.group(1)) + 1) * len(m.group(2).split()) if m.group(1) else 1
               for m in re.finditer(r"D(\d+)\(([^)]*)\)|[a-z]+", body))


class _Skel:
    def __init__(self, text):
        self.t, self.i = _SKEL.findall(text), 0
        assert "".join(self.t).replace(" ", "") == text.replace(" ", ""), text

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, want=None):
        tok = self.t[self.i]
        assert want is None or tok == want, (want, self.t)
        self.i += 1
        return tok

    def node(self):
        if self.peek().startswith("{"):
            return ("phr", _phrase_tokens(self.take()[1:-1]))
        self.take("(")
        if self.peek() == "tan":
            self.take(); ex = self.expr(); self.take("la"); body = self.node(); self.take(")")
            return ("srcctx", ex, body)
        first = self.node()
        word = self.peek()
        if word == "anu":
            self.take(); right = self.expr(); self.take(")")
            return ("alt", first, right)
        if word == "li":
            preds = []
            while self.peek() == "li":
                self.take(); preds.append(self.pred())
            self.take(")")
            return ("clause", first, preds)
        self.take("la"); body = self.node(); self.take(")")
        return ("ctx", first, body)

    def expr(self):
        n = self.node()
        assert n[0] in ("phr", "alt"), n
        return n

    def pred(self):
        head, objs, srcs = None, [], []
        if self.peek() == "tan":
            self.take(); srcs.append(self.expr())
        else:
            head = self.expr()
        while self.peek() == "e":
            self.take(); objs.append(self.expr())
        while self.peek() == "tan":
            self.take(); srcs.append(self.expr())
        return head, objs, srcs


def _short(n, nominal, why, out):
    if n[0] == "phr":
        if nominal and n[1] < 2:
            out.append(why)
    else:
        _short(n[1], nominal, why, out)
        _short(n[2], nominal, why, out)


def _clause_n2(n, out, bare=False):
    if n[0] in ("phr", "alt"):
        return _short(n, not bare, "context", out)
    _short(n[1], True, "subject", out)
    for head, objs, srcs in n[2]:
        if head:
            _short(head, False, "predicate", out)
        for o in objs:
            _short(o, True, "object", out)
        for x in srcs:
            _short(x, True, "source", out)


def n2_violations(skeleton):
    """Positions in which a skeleton holds a one-token nominal phrase (empty = N2-valid)."""
    p = _Skel(skeleton)
    n = p.node()
    assert p.i == len(p.t), skeleton
    out = []
    if n[0] == "ctx":
        _clause_n2(n[1], out); _clause_n2(n[2], out)
    elif n[0] == "srcctx":
        _short(n[1], True, "source context", out); _clause_n2(n[2], out)
    else:
        _clause_n2(n, out, bare=True)
    return out


def test_the_n2_skeleton_checker_flags_known_negatives_and_passes_known_positives():
    assert n2_violations("({ilo} li {awen})") == ["subject"]
    assert n2_violations("({jan pali} li {pali} e {ilo})") == ["object"]
    assert n2_violations("({jan pali} li tan {ma})") == ["source"]
    assert n2_violations("(tan {ni} la ({jan pali} li {pali}))") == ["source context"]
    assert n2_violations("({ma} la ({ilo pali} li {awen}))") == ["context"]
    assert n2_violations("({jan pali} li {pali} e ({ilo sitelen} anu {ijo}))") == ["object"]
    assert n2_violations("(({jan} li {pali}) la ({ilo pali} li {awen}))") == ["subject"]
    assert n2_violations("({ilo pali} li {awen})") == []
    assert n2_violations("{pali}") == [] and n2_violations("({pali} anu {awen})") == []
    assert n2_violations("({jan ni} li {lukin} e {D1(ilo)})") == []
    assert n2_violations("({jan pi ilo sona} li {pana} e {ilo pi sona lawa})") == []
    assert n2_violations("({jan pali} li {pona} e ({ilo pali} anu {ijo ni}))") == []


def test_no_expected_skeleton_of_the_corpus_holds_a_one_token_nominal_phrase():
    bad = {}
    for _f, _n, r in RECORDS:
        for sk in r.get("expect_skeletons", []):
            if n2_violations(sk):
                bad.setdefault(r["id"], []).append(sk)
    assert bad == {}


def test_every_record_that_n2_rewrote_carries_a_decision_field_and_says_so():
    marker = "author decision 2026-10-28"
    for f, _n, r in RECORDS:
        if f == N2_FILE:
            continue
        text = r.get("note", "") + r.get("rationale", "")
        if "N2 rewrite" in text:
            assert marker in r.get("decision", ""), r["id"]
            assert marker in text, r["id"]
        else:
            assert "decision" not in r or marker not in r["decision"] or r["id"] in ("k20", "k21"), r["id"]


def test_the_n2_file_holds_the_nineteen_worked_examples_and_the_extras():
    recs = [r for f, _n, r in RECORDS if f == N2_FILE]
    assert [r["id"] for r in recs] == ["canon-n2-%02d" % i for i in range(1, len(recs) + 1)]
    assert len(recs) >= 19 + 6
    spec = {1: "INVALID", 2: "RESOLVED", 3: "RESOLVED", 4: "RESOLVED", 5: "INVALID", 6: "RESOLVED",
            7: "INVALID", 8: "RESOLVED", 9: "RESOLVED", 10: "RESOLVED", 11: "INVALID", 12: "RESOLVED",
            13: "INVALID", 14: "RESOLVED", 15: "INVALID", 16: "RESOLVED", 17: "INVALID",
            18: "RESOLVED", 19: "RESOLVED"}
    assert {i: recs[i - 1]["expect_status"] for i in spec} == spec
    # known-negative: the INVALID worked examples are exactly the ones whose RESOLVED twin passes
    assert recs[0]["surface"] == "ilo li awen" and recs[1]["surface"] == "ilo pali li awen"


def test_n2_strictness_over_valid_toki_pona_is_declared_in_the_compat_file():
    compat = {r["id"]: r for f, _n, r in RECORDS if f == "toki_pona_compat.jsonl"}
    for i, surface in (("k20", "ilo li pona"), ("k21", "jan li pali e ilo")):
        assert compat[i]["surface"] == surface and compat[i]["expect_status"] == "INVALID"
        assert "VALID Toki Pona; rejected as OpenPona strictness" in compat[i]["note"]
        assert "2026-10-28" in compat[i]["note"]
