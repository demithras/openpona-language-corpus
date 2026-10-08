"""TP-03: record profiles (ParsedStatement / BoundStatement / AgentEvent) and the binding validator.

Collected by `python -m pytest -q` like every other test.  The 42 tokens are read from
data/matrix.csv at test time; nothing here hand-copies the inventory.
"""
import copy
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import openpona
from openpona import TOKENS, parse
from openpona import binding as B
from openpona import _schemacheck as SC
from openpona import record_schemas as RS

ROOT = Path(__file__).resolve().parent.parent
VALID_DIR = ROOT / "examples" / "records" / "valid"
INVALID_DIR = ROOT / "examples" / "records" / "invalid"
SCHEMA_DIR = ROOT / "schema" / "profiles"
REV = "graph-rev:test@1"

REQUIRED_INVALID = {
    "conflicting_bound_ref.json": "conflicting_bound_ref",
    "missing_critical_field.json": "missing_required_field",
    "unknown_key.json": "unknown_key",
    "ast_subject_mismatch.json": "ast_subject_mismatch",
    "unbound_ambiguous_address.json": "unbound_ambiguous_address",
    "non_canonical_token.json": "non_canonical_token",
    "authorization_from_truth_status.json": "authorization_from_truth_status",
}


def matrix_tokens() -> set:
    with (ROOT / "data" / "matrix.csv").open(newline="", encoding="utf-8") as fh:
        return {r["token"] for r in csv.DictReader(fh)}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def story() -> list:
    return [load(p) for p in sorted(VALID_DIR.glob("agent_event_ci_story_*.json"))]


def codes(record) -> set:
    return {i.code for i in B.validate_record(record).issues}


def resealed(record) -> dict:
    return B.seal_record(record, record["binding_seal"]["source_revision"])


def cli(*args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "openpona", *args], cwd=ROOT,
                          capture_output=True, text=True, timeout=120)


def ent(tokens, ref):
    return {"tokens": list(tokens), "resolution_status": "RESOLVED", "bound_ref": ref}


def build_bound(surface: str, idx: int = 0) -> dict:
    """A BoundStatement derived mechanically from the AST roles of `surface`."""
    res = parse(surface)
    roles = B.ast_roles(res.alternatives[idx])
    rec = {"profile": "BoundStatement", "schema_version": RS.SCHEMA_VERSION,
           "token_version": RS.TOKEN_VERSION, "surface": " ".join(res.tokens),
           "tokens": list(res.tokens), "parse_reference": B.parse_reference_for(surface, idx),
           "resolution_status": "RESOLVED", "resolution_context": ["project:t"]}
    ref = lambda toks: "ent:" + "-".join(toks)
    for role in ("subject", "context"):
        if roles[role]:
            rec[role] = ent(roles[role], ref(roles[role]))
    if roles["objects"]:
        rec["object"] = ent(roles["objects"][0], ref(roles["objects"][0]))
    if roles["predicates"]:
        rec["predicate"] = {"tokens": roles["predicates"][0]}
    return B.seal_record(rec, REV)


# ------------------------------------------------------------------ schema files
@pytest.mark.parametrize("profile", RS.PROFILES)
def test_committed_schema_equals_generator_output(profile):
    path = SCHEMA_DIR / RS.FILES[profile]
    assert path.read_text(encoding="utf-8") == RS.dumps(RS.build_schema(profile))


@pytest.mark.parametrize("profile", RS.PROFILES)
def test_token_enum_is_the_42_tokens_of_matrix_csv(profile):
    schema = json.loads((SCHEMA_DIR / RS.FILES[profile]).read_text(encoding="utf-8"))
    enum = schema["$defs"]["token"]["enum"]
    want = matrix_tokens()
    assert len(want) == 42 and len(enum) == 42 and set(enum) == want
    assert set(TOKENS) == want          # the packaged table agrees; no 43rd token anywhere


def _walk(node, path=""):
    yield path, node
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}/{i}")


@pytest.mark.parametrize("profile", RS.PROFILES)
def test_every_tokens_array_goes_through_the_token_enum(profile):
    schema = json.loads((SCHEMA_DIR / RS.FILES[profile]).read_text(encoding="utf-8"))
    seen = 0
    for path, node in _walk(schema):
        if path.endswith("/properties/tokens"):
            seen += 1
            assert node == {"$ref": "#/$defs/tokens"}, path
    assert seen >= 2 if profile != "ParsedStatement" else seen >= 1
    assert schema["$defs"]["tokens"]["items"] == {"$ref": "#/$defs/token"}
    # the only enums in the schema that are lists of tokens are the token def
    for path, node in _walk(schema):
        if isinstance(node, dict) and "enum" in node and set(node["enum"]) & matrix_tokens():
            assert path == "/$defs/token", path


@pytest.mark.parametrize("profile", RS.PROFILES)
def test_profiles_declare_versions_and_parse_reference(profile):
    schema = json.loads((SCHEMA_DIR / RS.FILES[profile]).read_text(encoding="utf-8"))
    for key in ("profile", "schema_version", "token_version", "parse_reference", "surface", "tokens"):
        assert key in schema["required"], key
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert schema["properties"]["token_version"] == {"const": manifest["token_version"]}
    assert schema["properties"]["profile"] == {"const": profile}
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("profile", RS.PROFILES)
def test_every_object_in_a_strict_profile_rejects_unknown_keys_except_x(profile):
    schema = json.loads((SCHEMA_DIR / RS.FILES[profile]).read_text(encoding="utf-8"))
    objects = 0
    for path, node in _walk(schema):
        if isinstance(node, dict) and node.get("type") == "object" and "properties" in node:
            objects += 1
            assert node.get("additionalProperties") is False, path
            assert node.get("patternProperties") == {RS.X_PATTERN: {}}, path
    assert objects >= 1
    # literals is the single free-form map, and says so
    lit = schema["$defs"]["literals"]
    assert lit["type"] == "object" and "properties" not in lit


def test_profiles_have_no_authorization_field():
    for profile in RS.PROFILES:
        schema = RS.build_schema(profile)
        for path, node in _walk(schema):
            if path.endswith("/properties") and isinstance(node, dict):
                assert not [k for k in node if B._auth_key(k)], (profile, path)


def test_schema_version_and_token_version_are_distinct_identifiers():
    assert RS.SCHEMA_VERSION != RS.TOKEN_VERSION != openpona.PARSER_API_VERSION
    assert RS.TOKEN_VERSION == json.loads((ROOT / "MANIFEST.json").read_text())["token_version"]


# ------------------------------------------------------------- mini schema checker
def test_schemacheck_refuses_keywords_it_does_not_implement():
    with pytest.raises(SC.SchemaError):
        SC.check({"type": "object", "oneOf": []}, {})
    with pytest.raises(SC.SchemaError):
        SC.check({"$ref": "https://example.org/x.json"}, {})
    with pytest.raises(SC.SchemaError):
        SC.check({"type": "string", "format": "email"}, "a@b")


def test_schemacheck_semantics():
    s = {"type": "object", "required": ["a"], "properties": {"a": {"type": "integer"}},
         "additionalProperties": False}
    assert SC.check(s, {"a": 1}) == []
    assert [i.keyword for i in SC.check(s, {"a": True})] == ["type"]      # bool is not integer
    assert [i.keyword for i in SC.check(s, {"a": 1.5})] == ["type"]
    assert {i.keyword for i in SC.check(s, {"b": 1})} == {"required", "additionalProperties"}
    assert SC.check({"const": 1}, True) != []                                # True != 1
    assert SC.check({"type": ["string", "null"]}, None) == []
    assert SC.check({"type": "array", "uniqueItems": True}, [1, 1]) != []
    assert SC.check({"type": "array", "uniqueItems": True}, [1, True]) == []
    cond = {"if": {"properties": {"k": {"const": 1}}, "required": ["k"]},
            "then": {"required": ["v"]}}
    assert SC.check(cond, {"k": 2}) == []
    out = SC.check(cond, {"k": 1})
    assert [i.keyword for i in out] == ["required"] and out[0].conditional


@pytest.mark.parametrize("value,ok", [
    ("2026-10-08T09:30:00Z", True), ("2026-10-08T09:30:00.5+03:00", True),
    ("2026-10-08t09:30:00z", False), ("2026-10-08 09:30:00Z", False),
    ("2026-10-08T09:30:00", False), ("2026-02-30T09:30:00Z", False),
    ("2026-10-08T24:30:00Z", False), ("2026-10-08T09:30:00+24:00", False),
    ("2026-10-08", False), ("", False),
])
def test_rfc3339(value, ok):
    assert SC.is_rfc3339(value) is ok


# --------------------------------------------------------------------- examples
def test_valid_examples_include_the_ci_story_and_all_three_profiles():
    files = sorted(VALID_DIR.glob("*.json"))
    assert len(files) >= 3
    profiles = {load(f)["profile"] for f in files}
    assert profiles == set(RS.PROFILES)
    assert len(story()) == 7


@pytest.mark.parametrize("path", sorted(VALID_DIR.glob("*.json")), ids=lambda p: p.name)
def test_valid_example_validates_against_its_declared_profile(path):
    rec = load(path)
    res = B.validate_record(rec, rec["profile"])
    assert res.valid, [str(i) for i in res.issues]
    assert res.profile == rec["profile"]


def test_invalid_examples_have_exactly_the_required_names():
    names = {p.name for p in INVALID_DIR.glob("*.json")}
    assert set(REQUIRED_INVALID) - names == set()
    assert names == set(REQUIRED_INVALID)


@pytest.mark.parametrize("name,code", sorted(REQUIRED_INVALID.items()))
def test_invalid_example_fails_with_exactly_its_typed_reason(name, code):
    res = B.validate_file(INVALID_DIR / name)
    assert not res.valid
    assert res.reason == code
    assert {i.code for i in res.issues} == {code}, [str(i) for i in res.issues]


def test_each_invalid_example_is_a_one_defect_variant_of_a_valid_one():
    """Remove the defect and the record becomes valid: the example fails for the named
    reason and for no other (checked by repairing the one thing)."""
    ev1, ev2 = story()[0], story()[1]
    ok = {}
    m = load(INVALID_DIR / "missing_critical_field.json")
    m["created_at"] = ev1["created_at"]
    ok["missing_critical_field"] = m
    k = load(INVALID_DIR / "unknown_key.json")
    del k["severity"]
    ok["unknown_key"] = k
    z = load(INVALID_DIR / "authorization_from_truth_status.json")
    del z["authorization"]
    ok["authorization_from_truth_status"] = z
    a = load(INVALID_DIR / "ast_subject_mismatch.json")
    a["subject"] = copy.deepcopy(ev1["subject"])
    ok["ast_subject_mismatch"] = resealed(a)
    u = load(INVALID_DIR / "unbound_ambiguous_address.json")
    u["subject"] = copy.deepcopy(ev1["subject"])
    ok["unbound_ambiguous_address"] = resealed(u)
    c = load(INVALID_DIR / "conflicting_bound_ref.json")
    c["object"]["bound_ref"] = c["subject"]["bound_ref"]
    ok["conflicting_bound_ref"] = resealed(c)
    n = load(INVALID_DIR / "non_canonical_token.json")
    n["surface"] = ev1["surface"]
    n["tokens"] = list(ev1["tokens"])
    n["parse_reference"] = copy.deepcopy(ev1["parse_reference"])
    n["subject"] = copy.deepcopy(ev1["subject"])
    n["context"] = copy.deepcopy(ev1["context"])
    n["evidence_refs"] = list(ev1["evidence_refs"])
    n["truth_status"] = "observed"
    ok["non_canonical_token"] = resealed(n)
    assert set(ok) == {c.removesuffix(".json") for c in REQUIRED_INVALID}
    for name, rec in ok.items():
        res = B.validate_record(rec)
        assert res.valid, (name, [str(i) for i in res.issues])
    assert ev2["truth_status"] == "requested"


def test_cli_classifies_every_example_and_names_the_reason():
    wrong, missing = set(), set(REQUIRED_INVALID) - {p.name for p in INVALID_DIR.glob("*.json")}
    for f in sorted(VALID_DIR.glob("*")):
        if cli("validate-record", str(f)).returncode != 0:
            wrong.add(f.name)
    for f in sorted(INVALID_DIR.glob("*")):
        r = cli("validate-record", str(f))
        if r.returncode == 0:
            wrong.add(f.name)
        elif f.name in REQUIRED_INVALID:
            assert r.stdout.splitlines()[0] == f"invalid: {REQUIRED_INVALID[f.name]}", r.stdout
            assert r.returncode == 1
    assert wrong == set() and missing == set()


def test_cli_edge_cases(tmp_path):
    r = cli("validate-record", str(tmp_path / "nope.json"))
    assert r.returncode == 1 and r.stdout.startswith("invalid: unreadable_file")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    r = cli("validate-record", str(bad))
    assert r.returncode == 1 and r.stdout.startswith("invalid: invalid_json")
    arr = tmp_path / "arr.json"
    arr.write_text("[1]", encoding="utf-8")
    assert cli("validate-record", str(arr)).stdout.startswith("invalid: not_an_object")
    noprof = tmp_path / "p.json"
    noprof.write_text("{}", encoding="utf-8")
    assert cli("validate-record", str(noprof)).stdout.startswith("invalid: missing_profile")
    noprof.write_text('{"profile": "Other"}', encoding="utf-8")
    assert cli("validate-record", str(noprof)).stdout.startswith("invalid: unknown_profile")
    ok = cli("validate-record", str(next(iter(sorted(VALID_DIR.glob("*.json"))))))
    assert ok.returncode == 0 and ok.stdout.startswith("valid: ")


def test_cli_persisted_flag_detects_a_rewritten_binding(tmp_path):
    old = story()[2]
    new = copy.deepcopy(old)
    new["object"]["bound_ref"] = "ci:run-9999"
    new = resealed(new)           # a re-sealed rewrite passes the single-record check ...
    assert B.validate_record(new).valid
    (tmp_path / "old.json").write_text(json.dumps(old), encoding="utf-8")
    (tmp_path / "new.json").write_text(json.dumps(new), encoding="utf-8")
    r = cli("validate-record", str(tmp_path / "new.json"), "--persisted", str(tmp_path / "old.json"))
    assert r.returncode == 1 and r.stdout.startswith("invalid: bound_ref_rewritten")
    same = cli("validate-record", str(tmp_path / "old.json"), "--persisted", str(tmp_path / "old.json"))
    assert same.returncode == 0


# ------------------------------------------------ the story: requested/intended/observed
def test_story_events_match_the_walkthrough_closing_block():
    text = (ROOT / "examples" / "walkthrough_ci_failure.md").read_text(encoding="utf-8")
    block = text.split("## The whole story in order", 1)[1]
    fence = re.search(r"```openpona\n(.*?)```", block, re.S).group(1)
    lines = [ln.split(" # ", 1)[0].strip() for ln in fence.splitlines() if ln.strip()]
    assert [e["surface"] for e in story()] == lines and len(lines) == 7


def test_story_statuses_are_in_the_field_not_the_surface():
    ev = story()
    assert [e["truth_status"] for e in ev] == [
        "observed", "requested", "intended", "intended", "observed", "intended", "observed"]
    assert ev[1]["actor"] != ev[0]["actor"]          # the colleague asked, the agent observes
    # the three statuses are distinct values of one required field
    assert len({e["truth_status"] for e in ev}) == 3
    assert "truth_status" in json.loads((SCHEMA_DIR / "agent_event.schema.json").read_text())["required"]
    # flipping the field changes the record's status and nothing in the surface tokens
    flipped = copy.deepcopy(ev[1])
    flipped["truth_status"] = "intended"
    assert B.validate_record(flipped).valid and flipped["surface"] == ev[1]["surface"]
    # the validator never reads a status prefix (research convention H-TS) off the tokens
    assert flipped["tokens"] == ev[1]["tokens"] and flipped["truth_status"] != ev[1]["truth_status"]


def test_every_story_event_is_fully_bound_and_chained():
    ids = []
    for e in story():
        assert e["resolution_status"] == "RESOLVED"
        for role in ("subject", "object", "context"):
            if role in e:
                assert e[role]["resolution_status"] == "RESOLVED" and e[role]["bound_ref"]
        ids.append(e["statement_id"])
        for c in e.get("cause_refs", []):
            assert c in ids          # causes point backwards
    assert len(set(ids)) == 7
    stamps = [e["created_at"] for e in story()]
    assert stamps == sorted(stamps) and len(set(stamps)) == 7


def test_observed_events_carry_evidence_and_others_may_omit_it():
    ev = story()
    for e in ev:
        if e["truth_status"] == "observed":
            assert e["evidence_refs"]
        else:
            assert "evidence_refs" not in e and B.validate_record(e).valid
    e = copy.deepcopy(ev[0])
    del e["evidence_refs"]
    assert codes(e) == {"observed_without_evidence"}
    e["evidence_refs"] = []
    assert codes(e) == {"observed_without_evidence"}
    # optional evidence on a non-observed status is fine
    r = copy.deepcopy(ev[1])
    r["evidence_refs"] = ["msg:colleague-ask"]
    assert B.validate_record(r).valid


# ---------------------------------------------------- required fields and strictness
AGENT_REQUIRED = json.loads((SCHEMA_DIR / "agent_event.schema.json").read_text())["required"]


@pytest.mark.parametrize("field", AGENT_REQUIRED)
def test_removing_any_required_agent_event_field_is_rejected(field):
    rec = copy.deepcopy(story()[0])
    del rec[field]
    res = B.validate_record(rec)
    assert not res.valid
    if field in ("profile",):
        assert res.reason == "missing_profile"
    else:
        assert "missing_required_field" in {i.code for i in res.issues}


@pytest.mark.parametrize("field", ["statement_id", "created_at", "actor", "truth_status", "provenance"])
def test_persisted_event_fields_are_required_in_agent_event_but_optional_in_bound(field):
    assert field in AGENT_REQUIRED
    bound = json.loads((SCHEMA_DIR / "bound_statement.schema.json").read_text())
    assert field not in bound["required"] and field in bound["properties"]


def test_unknown_keys_rejected_at_every_nesting_level_and_x_keys_allowed():
    base = story()[2]
    base = copy.deepcopy(base)
    base["predicate"] = {"tokens": ["pona"]}
    base = resealed(base)
    assert B.validate_record(base).valid
    for where in (None, "parse_reference", "binding_seal", "provenance", "subject", "object",
                  "context", "predicate"):
        bad = copy.deepcopy(base)
        (bad if where is None else bad[where])["bogus"] = 1
        res = B.validate_record(bad)
        assert {i.code for i in res.issues} == {"unknown_key"}, where
        assert res.issues[0].path.endswith("/bogus")
        ok = copy.deepcopy(base)
        (ok if where is None else ok[where])["x-bogus"] = {"anything": [1, None, "z"]}
        assert B.validate_record(ok).valid, where          # extension keys: allowed, unsealed
        assert B.check_immutable(base, ok) == []           # ... and not "history rewriting"
    for key in ("x-", "x", "X-foo", "x_foo", "xfoo", "x-a b"):
        bad = copy.deepcopy(base)
        bad[key] = 1
        assert codes(bad) == {"unknown_key"}, key


def test_parsed_statement_carries_no_binding_or_truth():
    p = load(VALID_DIR / "parsed_statement.json")
    for key in ("truth_status", "actor", "subject", "resolution_status", "binding_seal",
                "parse_status", "authorization"):
        bad = copy.deepcopy(p)
        bad[key] = "observed" if key == "truth_status" else {}
        assert not B.validate_record(bad).valid, key
        assert "unknown_key" in codes(bad) or "authorization_from_truth_status" in codes(bad)


def test_created_at_must_be_rfc3339():
    for bad in ("2026-10-08 09:00:00Z", "2026-10-08T09:00:00", "yesterday", "2026-13-01T00:00:00Z", 5):
        e = copy.deepcopy(story()[0])
        e["created_at"] = bad
        assert codes(e) & {"bad_timestamp", "wrong_type"}, bad
    for good in ("2026-10-08T09:00:00+03:00", "2026-10-08T09:00:00.250Z"):
        e = copy.deepcopy(story()[0])
        e["created_at"] = good
        assert B.validate_record(e).valid, good


def test_versions_are_pinned():
    e = copy.deepcopy(story()[0])
    e["token_version"] = "anu 1.2"
    assert codes(e) == {"token_version_mismatch"}
    e = copy.deepcopy(story()[0])
    e["schema_version"] = "records-2.0.0"
    assert codes(e) == {"schema_version_unsupported"}
    e = copy.deepcopy(story()[0])
    e["profile"] = "BoundStatement"
    # declared profile decides the schema: an AgentEvent body under BoundStatement is valid
    assert B.validate_record(e).profile == "BoundStatement"
    assert B.validate_record(story()[0], "BoundStatement").reason == "profile_mismatch"


def test_provenance_source_event_needs_a_source():
    e = copy.deepcopy(story()[6])
    del e["provenance"]["source_event"]
    assert codes(e) == {"provenance_source_missing"}
    e["provenance"]["kind"] = "made_up"
    assert "invalid_value" in codes(e)


# ----------------------------------------------------------------- token constraint
def test_non_canonical_tokens_rejected_in_every_tokens_array():
    for bad in ("sin", "mi", "o", "en", "mute", "Jan", "", "42", "ilo pali"):
        e = copy.deepcopy(story()[2])
        e["tokens"][3] = bad
        assert "non_canonical_token" in codes(e), bad
        e = copy.deepcopy(story()[2])
        e["subject"]["tokens"][0] = bad
        assert "non_canonical_token" in codes(e), bad
    for role in ("subject", "object", "context"):
        e = copy.deepcopy(story()[2])
        e[role]["tokens"] = []
        assert not B.validate_record(e).valid


@pytest.mark.parametrize("tok", sorted(matrix_tokens()))
def test_each_of_the_42_tokens_is_accepted_by_the_enum(tok):
    defs = RS.build_schema("AgentEvent")["$defs"]
    probe = {"$ref": "#/$defs/tokens", "$defs": defs}
    assert SC.check(probe, [tok]) == []
    assert SC.check(probe, [tok + "x"]) != []


# ----------------------------------------------------- parser cross-check (surface)
def test_surface_is_cross_checked_with_the_parser():
    e = copy.deepcopy(story()[0])
    e["tokens"] = e["tokens"][:-1]
    assert codes(e) == {"surface_tokens_mismatch"}
    # a surface the parser rejects, with a syntactically complete record
    bad = build_bound("ilo pali li pona")
    bad["surface"] = "jan ilo sona"
    bad["tokens"] = bad["surface"].split()
    assert parse(bad["surface"]).status == "INVALID"
    assert "surface_parse_invalid" in codes(resealed(bad))


def test_unavailable_parse_verdict_is_not_pinned(monkeypatch):
    rec = story()[0]

    class Fake:
        status, alternatives, errors, tokens = "RESOURCE_EXHAUSTED", (), ["budget"], rec["tokens"]
    monkeypatch.setattr(B, "parse", lambda s: Fake)
    assert "surface_parse_unavailable" in codes(rec)


def test_parse_reference_pin_is_checked():
    base = story()[0]
    for field, value, code in (
        ("status", "AMBIGUOUS", "parse_reference_mismatch"),
        ("alternative_index", 3, "parse_reference_mismatch"),
        ("ast_sha256", "0" * 64, "parse_reference_mismatch"),
        ("api_version", "2.0.0", "parse_api_incompatible"),
    ):
        e = copy.deepcopy(base)
        e["parse_reference"][field] = value
        assert codes(resealed(e)) == {code}, field
    e = copy.deepcopy(base)
    e["parse_reference"]["api_version"] = "1.9.9"         # same major, digest still decides
    assert B.validate_record(resealed(e)).valid
    e["parse_reference"]["status"] = "INVALID"
    assert "invalid_value" in codes(e)


def test_ambiguous_parse_pins_one_reading_and_digests_differ():
    surface = "jan pali jan pali jan"
    res = parse(surface)
    assert res.status == "AMBIGUOUS" and len(res.alternatives) == 2
    refs = [B.parse_reference_for(surface, i) for i in (0, 1)]
    assert refs[0]["ast_sha256"] != refs[1]["ast_sha256"] and refs[0]["status"] == "AMBIGUOUS"
    for i in (0, 1):
        assert B.validate_record(build_bound(surface, i)).valid
    # pin reading 0 but carry reading 1's digest: refused
    bad = build_bound(surface, 0)
    bad["parse_reference"]["ast_sha256"] = refs[1]["ast_sha256"]
    assert codes(resealed(bad)) == {"parse_reference_mismatch"}
    with pytest.raises(ValueError):
        B.parse_reference_for(surface, 2)
    with pytest.raises(ValueError):
        B.parse_reference_for("jan ilo sona")


# ----------------------------------------------------- AST role cross-check
def test_subject_object_context_predicate_are_checked_against_the_ast():
    ev = story()[2]       # ma pali la jan linja li pona e ilo pali
    cases = [
        ("subject", ["kulupu", "pali"], "ast_subject_mismatch"),
        ("subject", ["jan"], "ast_subject_mismatch"),
        ("object", ["tenpo", "linja"], "ast_object_mismatch"),
        ("object", ["ilo"], "ast_object_mismatch"),
        ("context", ["ma"], "ast_context_mismatch"),
        ("context", ["sike", "pali"], "ast_context_mismatch"),
    ]
    for role, toks, code in cases:
        e = copy.deepcopy(ev)
        e[role]["tokens"] = toks
        assert codes(resealed(e)) == {code}, (role, toks)
    e = copy.deepcopy(ev)
    e["predicate"] = {"tokens": ["pona"]}
    assert B.validate_record(resealed(e)).valid
    e["predicate"] = {"tokens": ["pali"]}
    assert codes(resealed(e)) == {"ast_predicate_mismatch"}
    # swapped subject / object are both reported (typed, with the AST's own answer)
    e = copy.deepcopy(ev)
    e["subject"]["tokens"], e["object"]["tokens"] = ev["object"]["tokens"], ev["subject"]["tokens"]
    res = B.validate_record(resealed(e))
    assert {i.code for i in res.issues} == {"ast_subject_mismatch", "ast_object_mismatch"}
    assert "[jan linja]" in next(i for i in res.issues if i.code == "ast_subject_mismatch").message


def test_sidecar_is_not_trusted_even_when_internally_consistent_and_resealed():
    e = copy.deepcopy(story()[0])        # subject is [ilo pali]; claim it was [jan pali]
    e["subject"] = ent(["jan", "pali"], "urn:person:x")
    assert codes(resealed(e)) == {"ast_subject_mismatch"}


def test_missing_binding_for_ast_subject_and_context():
    for role in ("subject", "context"):
        e = copy.deepcopy(story()[0])
        del e[role]
        assert codes(resealed(e)) == {"missing_binding"}, role
    # objects are optional (a state is not an entity)
    e = copy.deepcopy(story()[2])
    del e["object"]
    assert B.validate_record(resealed(e)).valid


def test_binding_a_role_the_ast_does_not_have():
    rec = build_bound("ilo pali")                       # a bare phrase: no subject, no object
    rec["subject"] = ent(["ilo", "pali"], "ci:run-1")
    assert codes(resealed(rec)) == {"ast_subject_mismatch"}
    rec = build_bound("ilo pali li pona")
    rec["context"] = ent(["ma", "pali"], "project:x")
    assert codes(resealed(rec)) == {"ast_context_mismatch"}
    # a source context (tan X la ...) is not a resolution context
    rec = build_bound("tan ilo pali la jan li pona")
    assert "context" not in rec
    rec["context"] = ent(["ilo", "pali"], "ci:run-1")
    assert codes(resealed(rec)) == {"ast_context_mismatch"}


NON_INVALID = [json.loads(ln) for p in sorted((ROOT / "conformance").glob("*.jsonl"))
               for ln in p.read_text(encoding="utf-8").splitlines()
               if ln.strip() and json.loads(ln)["expect_status"] != "INVALID"]


@pytest.mark.parametrize("case", NON_INVALID, ids=[c["id"] for c in NON_INVALID])
def test_records_built_from_the_ast_validate_and_role_swaps_are_detected(case):
    surface = case["surface"]
    n = len(parse(surface).alternatives)
    for idx in range(n):
        rec = build_bound(surface, idx)
        res = B.validate_record(rec)
        assert res.valid, (case["id"], idx, [str(i) for i in res.issues])
        roles = B.ast_roles(parse(surface).alternatives[idx])
        fresh = [next(t for t in sorted(TOKENS) if t not in rec["tokens"])]   # collides with nothing
        if roles["subject"]:
            bad = copy.deepcopy(rec)
            bad["subject"]["tokens"] = fresh
            assert codes(resealed(bad)) == {"ast_subject_mismatch"}, case["id"]
        if "object" in rec:
            bad = copy.deepcopy(rec)
            bad["object"]["tokens"] = fresh
            assert codes(resealed(bad)) == {"ast_object_mismatch"}, case["id"]
        if roles["context"]:
            bad = copy.deepcopy(rec)
            bad["context"]["tokens"] = fresh
            assert codes(resealed(bad)) == {"ast_context_mismatch"}, case["id"]


# ----------------------------------------------------------------- entity binding
def test_unbound_ambiguous_address_is_detected():
    amb = load(VALID_DIR / "bound_statement_ambiguous_ci_tool.json")
    assert B.validate_record(amb).valid                       # honest ambiguity is storable
    e = copy.deepcopy(amb)
    e["subject"]["resolution_status"] = "RESOLVED"            # claims resolved, still no ref
    assert codes(resealed(e)) == {"unbound_ambiguous_address", "resolution_status_mismatch"}
    e["resolution_status"] = "RESOLVED"                       # ... and the statement agrees
    assert codes(resealed(e)) == {"unbound_ambiguous_address"}
    e = copy.deepcopy(amb)
    e["resolution_status"] = "RESOLVED"                       # statement claims resolved
    assert codes(resealed(e)) == {"unbound_ambiguous_address"}
    e = copy.deepcopy(amb)
    e["subject"]["bound_ref"] = "ci:build-service"            # picked one: a guess
    assert codes(resealed(e)) == {"ambiguous_address_bound"}
    e = copy.deepcopy(amb)
    e["subject"]["candidates"] = ["ci:build-service"]          # one candidate is not ambiguity
    assert codes(resealed(e)) == {"binding_rule_violation"}


def test_conflicting_bound_ref_is_not_a_fully_bound_event():
    ev = load(INVALID_DIR / "conflicting_bound_ref.json")
    assert parse(ev["surface"]).status == "RESOLVED"          # the line itself is parse-valid
    res = B.validate_record(ev)
    assert not res.valid and res.reason == "conflicting_bound_ref"
    ev["object"]["bound_ref"] = ev["subject"]["bound_ref"]    # same address, same reference
    assert B.validate_record(resealed(ev)).valid
    # a bound_ref competing with other candidates is a guess among competitors
    e = copy.deepcopy(story()[0])
    e["subject"]["candidates"] = ["ci:run-4711", "ci:run-4712"]
    assert codes(resealed(e)) == {"conflicting_bound_ref"}
    e["subject"]["candidates"] = ["ci:run-4711"]
    assert B.validate_record(resealed(e)).valid


def test_other_binding_inconsistencies():
    e = copy.deepcopy(story()[0])
    del e["subject"]["bound_ref"]
    assert codes(resealed(e)) == {"missing_bound_ref"}
    q = load(VALID_DIR / "bound_statement_unresolved_question.json")
    assert q["parse_reference"]["status"] == "RESOLVED" and q["resolution_status"] == "UNRESOLVED"
    bad = copy.deepcopy(q)
    bad["subject"]["bound_ref"] = "x:y"
    assert not B.validate_record(resealed(bad)).valid
    bad = copy.deepcopy(story()[0])
    bad["resolution_status"] = "UNRESOLVED"
    assert codes(resealed(bad)) == {"resolution_status_mismatch"}


# ------------------------------------------------------------ authorization boundary
@pytest.mark.parametrize("status", ["requested", "intended", "observed", "asserted", "hypothesis"])
def test_authorization_cannot_ride_on_any_truth_status(status):
    e = copy.deepcopy(story()[0])
    e["truth_status"] = status
    assert B.validate_record(e).valid or status != "observed"
    e["authorized"] = True
    res = B.validate_record(e)
    assert res.reason == "authorization_from_truth_status"
    assert {i.code for i in res.issues} == {"authorization_from_truth_status"}


@pytest.mark.parametrize("key", ["authorized", "Authorization", "x-authorized", "x-may-execute",
                                 "may_execute", "permitted", "approved", "granted", "allowed",
                                 "execute", "authorisation", "x-action-authorization-basis"])
def test_authorization_like_keys_are_rejected_wherever_they_sit(key):
    for where in (None, "subject", "provenance", "parse_reference"):
        e = copy.deepcopy(story()[0])
        (e if where is None else e[where])[key] = {"granted": True}
        assert "authorization_from_truth_status" in codes(e), (where, key)


def test_authorization_scan_leaves_literals_and_other_x_values_alone():
    e = copy.deepcopy(story()[0])
    e["literals"]["authorized_by"] = "someone"               # data, not a decision field
    e["x-note"] = {"authorized": "free text inside an extension value"}
    assert B.validate_record(e).valid
    # an extension named for a decision is still rejected: the key is the claim
    e["x-authorization"] = True
    assert codes(e) == {"authorization_from_truth_status"}


def test_truth_status_values_are_those_of_the_legacy_schema():
    legacy = json.loads((ROOT / "schema" / "statement.schema.json").read_text())
    assert legacy["properties"]["truth_status"]["enum"] == RS.TRUTH_STATUSES


# ----------------------------------------------------------- immutability
def test_changing_context_after_persistence_does_not_change_bound_ref():
    old = story()[0]
    # (a) an in-place edit of the context is caught without any history
    edited = copy.deepcopy(old)
    edited["resolution_context"] = ["project:other"]
    assert codes(edited) == {"binding_seal_mismatch"}
    assert {i.code for i in B.check_immutable(old, edited)} == {"resolution_context_rewritten"}
    # (b) an in-place edit of a bound_ref likewise
    edited = copy.deepcopy(old)
    edited["subject"]["bound_ref"] = "ci:run-9999"
    assert codes(edited) == {"binding_seal_mismatch"}
    assert "bound_ref_rewritten" in {i.code for i in B.check_immutable(old, edited)}
    # (c) edit and re-seal: single-record check passes, the history check does not
    forged = resealed(edited)
    assert B.validate_record(forged).valid
    got = {i.code for i in B.check_immutable(old, forged)}
    assert {"bound_ref_rewritten", "binding_seal_rewritten"} <= got
    # (d) a seal is bound to its statement_id
    moved = copy.deepcopy(old)
    moved["statement_id"] = "acme-web-678-ev-99"
    assert codes(moved) == {"binding_seal_mismatch"}
    # (e) the sanctioned path: a NEW record that supersedes; the old one is untouched
    snapshot = copy.deepcopy(old)
    new = copy.deepcopy(old)
    new["statement_id"] = "acme-web-678-ev-01b"
    new["supersedes"] = old["statement_id"]
    new["resolution_context"] = ["project:acme-web", "repo:acme-web", "branch:hotfix"]
    new["subject"]["bound_ref"] = "ci:run-5000"
    new = B.seal_record(new, "graph-rev:acme-web@2026-10-09")
    assert B.validate_record(new).valid
    assert old == snapshot and old["subject"]["bound_ref"] == "ci:run-4711"
    assert B.check_immutable(old, snapshot) == []
    assert B.check_immutable(old, new)[0].code == "statement_id_mismatch"


def test_source_revision_is_part_of_the_seal():
    e = copy.deepcopy(story()[0])
    e["binding_seal"]["source_revision"] = "graph-rev:acme-web@later"
    assert codes(e) == {"binding_seal_mismatch"}
    assert B.validate_record(resealed(e)).valid


def test_truth_fields_are_not_sealed_but_are_immutable_in_history():
    old = story()[1]
    new = copy.deepcopy(old)
    new["truth_status"] = "intended"
    assert B.validate_record(new).valid                       # not part of the binding seal
    out = B.check_immutable(old, new)
    assert [i.code for i in out] == ["persisted_record_modified"] and "truth_status" in out[0].message


# --------------------------------------------------------------------- migration
LEGACY = {   # the record of walkthrough Step 3 plus the legacy-required fields
    "statement_id": "legacy-001", "surface": "ma pali la ilo pali li pona ala",
    "context": {"tokens": ["ma", "pali"], "bound_ref": "project:acme-web"},
    "subject": {"tokens": ["ilo", "pali"], "bound_ref": "ci:run-4711", "meta_depth": 0},
    "literals": {"pr_number": 678}, "actor": "urn:agent:linja",
    "resolution_context": ["project:acme-web", "repo:acme-web"],
    "resolution_status": "RESOLVED", "truth_status": "observed",
    "evidence": ["ci:check-run-9913"], "created_at": "2026-10-08T09:00:00Z",
    "parse_status": "RESOLVED", "branch": "main", "tokens": ["ma", "pali", "la"],
}


def test_migrate_legacy_record_to_agent_event():
    old = copy.deepcopy(LEGACY)
    snap = copy.deepcopy(old)
    new = B.migrate_legacy(old, source_revision="legacy-store@2026-10-08")
    assert old == snap                                        # the legacy record is not touched
    assert new["profile"] == "AgentEvent" and B.validate_record(new).valid
    assert new["subject"]["bound_ref"] == "ci:run-4711"
    assert new["provenance"] == {"kind": "legacy_migration"}
    assert new["x-legacy"]["branch"] == "main" and new["x-legacy"]["parse_status"] == "RESOLVED"
    assert new["x-legacy"]["subject"] == {"meta_depth": 0}
    assert new["binding_seal"]["source_revision"] == "legacy-store@2026-10-08"


def test_migrate_legacy_does_not_invent():
    old = copy.deepcopy(LEGACY)
    del old["resolution_context"], old["actor"]
    new = B.migrate_legacy(old, source_revision="r1")
    assert new["profile"] == "BoundStatement"
    assert new["resolution_context"] == []
    assert new["x-migration"]["resolution_context"].startswith("unknown")
    assert set(new["x-migration"]["missing_for_agent_event"]) == {"actor", "resolution_context"}
    assert B.validate_record(new).valid
    # ambiguity stays ambiguity, candidates are kept and nothing is bound
    amb = {"surface": "ma pali la ilo pali li pona ala", "context": {"tokens": ["ma", "pali"], "bound_ref": "project:a"},
           "subject": {"tokens": ["ilo", "pali"], "candidates": ["ci:a", "ci:b"]},
           "resolution_context": ["project:a"], "truth_status": "unknown"}
    m = B.migrate_legacy(amb, source_revision="r1")
    assert m["subject"]["resolution_status"] == "AMBIGUOUS" and "bound_ref" not in m["subject"]
    assert m["resolution_status"] == "AMBIGUOUS"
    # no candidates and no ref: UNRESOLVED
    unres = {"surface": "seme li tan e ni", "subject": {"tokens": ["seme"], "bound_ref": None}}
    assert B.migrate_legacy(unres, source_revision="r1")["subject"]["resolution_status"] == "UNRESOLVED"


def test_migrate_legacy_refusals():
    old = copy.deepcopy(LEGACY)
    del old["evidence"]
    with pytest.raises(B.MigrationError, match="observed"):
        B.migrate_legacy(old, source_revision="r1")
    with pytest.raises(B.MigrationError, match="does not parse"):
        B.migrate_legacy({"surface": "jan ilo sona"}, source_revision="r1")
    with pytest.raises(B.MigrationError, match="alternative_index"):
        B.migrate_legacy({"surface": "jan pali jan pali jan"}, source_revision="r1")
    assert B.migrate_legacy({"surface": "jan pali jan pali jan"}, source_revision="r1",
                            alternative_index=1)["parse_reference"]["alternative_index"] == 1
    with pytest.raises(B.MigrationError, match="token_version"):
        B.migrate_legacy({**LEGACY, "token_version": "anu 2.0"}, source_revision="r1")
    with pytest.raises(B.MigrationError, match="not valid"):
        B.migrate_legacy({**LEGACY, "created_at": "yesterday"}, source_revision="r1")


# -------------------------------------------------------------------------- docs
DOC = (ROOT / "docs" / "record-profiles.md").read_text(encoding="utf-8")
MIG = (ROOT / "docs" / "record-migration.md").read_text(encoding="utf-8")


def test_docs_document_every_code_profile_example_and_the_x_namespace():
    for code in B.ISSUE_CODES:
        assert f"`{code}`" in DOC, code
    for profile in RS.PROFILES:
        assert profile in DOC
    for name in REQUIRED_INVALID:
        assert name in DOC
    assert RS.X_PATTERN in DOC and "x-" in DOC
    for kind in RS.PROVENANCE_KINDS:
        assert f"`{kind}`" in DOC, kind
    assert "PENDING AUTHOR REVIEW" in DOC and "PENDING AUTHOR REVIEW" in MIG
    for word in ("append-only", "x-legacy", "x-migration", "MigrationError", "supersedes"):
        assert word.lower() in MIG.lower(), word


def test_issue_codes_are_closed():
    src = (ROOT / "openpona" / "binding.py").read_text(encoding="utf-8")
    used = set(re.findall(r'Issue\(\s*"([a-z_]+)"', src)) | set(
        re.findall(r'"([a-z_]+_(?:mismatch|unsupported|incompatible))"', src))
    assert used <= B.ISSUE_CODES
    with pytest.raises(ValueError):
        B.Issue("made_up_code", "", "")


def test_for_agents_points_at_the_profiles_without_changing_its_rules():
    text = (ROOT / "docs" / "for-agents.md").read_text(encoding="utf-8")
    assert "docs/record-profiles.md" in text and "validate-record" in text
    assert "A statement never grants permission" in text      # section 5 unchanged
    assert "History is immutable" in text


def test_schema_dir_has_exactly_the_three_profiles():
    assert {p.name for p in SCHEMA_DIR.glob("*.json")} == set(RS.FILES.values())


# ------------------------------------------------- optional full-validator cross-check
def test_profiles_agree_with_a_full_json_schema_validator_when_available():
    jsonschema = pytest.importorskip("jsonschema")
    pool = [load(p) for p in sorted(VALID_DIR.glob("*.json"))]
    pool += [load(p) for p in sorted(INVALID_DIR.glob("*.json"))]
    for name in AGENT_REQUIRED:
        r = copy.deepcopy(story()[0])
        r.pop(name, None)
        pool.append(r)
    r = copy.deepcopy(story()[0])
    r["tokens"][0] = "sin"
    pool.append(r)
    r = copy.deepcopy(story()[0])
    r["subject"] = {"tokens": ["ilo"], "resolution_status": "AMBIGUOUS", "bound_ref": "ci:x"}
    pool.append(r)
    for rec in pool:
        prof = rec.get("profile", "AgentEvent")
        schema = RS.build_schema(prof)
        v = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        theirs = not list(v.iter_errors(rec))
        ours = not SC.check(schema, rec)
        assert theirs == ours, (prof, rec.get("statement_id"), rec.get("x-defect"))
