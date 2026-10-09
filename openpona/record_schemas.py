"""Builder for the record profile schemas in `schema/profiles/` (TP-03).

ENGINEERING module.  The three profile files are GENERATED from this module so that
the 42-token enum is never hand-copied: it is taken from the packaged token table
(`openpona.TOKENS`), and `tests/test_records.py` compares both with the canonical
`data/matrix.csv` at test time and checks the committed files are byte-identical to
`build_schemas()` output.

    python -m openpona.record_schemas --write schema/profiles     # regenerate

Profiles (docs/record-profiles.md):

    ParsedStatement  syntax only: surface, tokens, parse_reference
    BoundStatement   + resolution_status, resolution_context, entity bindings, seal
    AgentEvent       + statement_id, created_at, actor, truth_status, provenance

Strict: every object rejects unknown keys except `x-...` extension keys.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

from . import TOKENS

SCHEMA_VERSION = "records-1.0.0"
TOKEN_VERSION = "anu 1.1"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
ID_BASE = ("https://raw.githubusercontent.com/demithras/openpona-language-corpus/"
           "main/schema/profiles/")
PROFILES = ("ParsedStatement", "BoundStatement", "AgentEvent")
FILES = {
    "ParsedStatement": "parsed_statement.schema.json",
    "BoundStatement": "bound_statement.schema.json",
    "AgentEvent": "agent_event.schema.json",
}
X_PATTERN = r"^x-[A-Za-z0-9][A-Za-z0-9._-]*$"
REF_PATTERN = r"^[A-Za-z][A-Za-z0-9+.-]*:[^\s]+$"
ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9:._/-]*$"
RFC3339_PATTERN = (r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
                   r"(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$")
TRUTH_STATUSES = ["observed", "asserted", "requested", "intended", "hypothesis",
                  "inferred", "unknown", "rejected"]   # same set as schema/statement.schema.json
RESOLUTION_STATUSES = ["RESOLVED", "AMBIGUOUS", "UNRESOLVED"]
PROVENANCE_KINDS = ["source_event", "runtime_observation", "agent_statement", "human_statement",
                    "legacy_migration"]
ENTITY_ROLES = ("subject", "object", "context")   # carry a binding
EXPRESSION_ROLES = ENTITY_ROLES + ("predicate",)   # appear as expression objects


def _strict(properties: dict, required: list[str], **extra) -> dict:
    """Object schema that rejects unknown keys except the `x-` extension namespace."""
    out = {"type": "object", "properties": properties, "required": required,
           "patternProperties": {X_PATTERN: {}}, "additionalProperties": False}
    out.update(extra)
    return out


def _defs() -> dict:
    status_is = lambda s: {"properties": {"resolution_status": {"const": s}},
                           "required": ["resolution_status"]}
    return {
        "token": {"enum": sorted(TOKENS)},
        "tokens": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/token"}},
        "ref": {"type": "string", "pattern": REF_PATTERN},
        "statement_id": {"type": "string", "pattern": ID_PATTERN},
        "rfc3339": {"type": "string", "format": "date-time", "pattern": RFC3339_PATTERN},
        "resolution_status": {"enum": RESOLUTION_STATUSES},
        "truth_status": {"enum": TRUTH_STATUSES},
        "parse_reference": _strict({
            "api_version": {"type": "string", "pattern": r"^[0-9]+\.[0-9]+\.[0-9]+$"},
            "status": {"enum": ["RESOLVED", "AMBIGUOUS"]},
            "alternative_index": {"type": "integer", "minimum": 0},
            "ast_sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
        }, ["api_version", "status", "alternative_index", "ast_sha256"]),
        "entity": _strict({
            "tokens": {"$ref": "#/$defs/tokens"},
            "resolution_status": {"$ref": "#/$defs/resolution_status"},
            "bound_ref": {"type": ["string", "null"], "pattern": REF_PATTERN},
            "candidates": {"type": "array", "items": {"$ref": "#/$defs/ref"},
                           "uniqueItems": True},
        }, ["tokens", "resolution_status"], allOf=[
            {"if": status_is("RESOLVED"),
             "then": {"required": ["bound_ref"],
                      "properties": {"bound_ref": {"type": "string"}}}},
            {"if": status_is("AMBIGUOUS"),
             "then": {"required": ["candidates"],
                      "properties": {"bound_ref": {"type": "null"},
                                     "candidates": {"minItems": 2}}}},
            {"if": status_is("UNRESOLVED"),
             "then": {"properties": {"bound_ref": {"type": "null"},
                                     "candidates": {"maxItems": 0}}}},
        ]),
        "predicate_expression": _strict({"tokens": {"$ref": "#/$defs/tokens"}}, ["tokens"]),
        "binding_seal": _strict({
            "algorithm": {"const": "sha256"},
            "source_revision": {"type": "string", "minLength": 1},
            "digest": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
        }, ["algorithm", "source_revision", "digest"]),
        "provenance": _strict({
            "kind": {"enum": PROVENANCE_KINDS},
            "source_event": {"type": "string", "minLength": 1},
        }, ["kind"], allOf=[
            {"if": {"properties": {"kind": {"const": "source_event"}}, "required": ["kind"]},
             "then": {"required": ["source_event"]}}]),
        "literals": {"type": "object", "additionalProperties":
                     {"type": ["string", "number", "boolean", "null"]}},
    }


def _common_props() -> dict:
    return {
        "schema_version": {"const": SCHEMA_VERSION},
        "token_version": {"const": TOKEN_VERSION},
        "surface": {"type": "string", "minLength": 1},
        "tokens": {"$ref": "#/$defs/tokens"},
        "parse_reference": {"$ref": "#/$defs/parse_reference"},
    }


def _bound_props() -> dict:
    return {
        "resolution_status": {"$ref": "#/$defs/resolution_status"},
        "resolution_context": {"type": "array", "items": {"$ref": "#/$defs/ref"},
                               "uniqueItems": True},
        "subject": {"$ref": "#/$defs/entity"},
        "object": {"$ref": "#/$defs/entity"},
        "context": {"$ref": "#/$defs/entity"},
        "predicate": {"$ref": "#/$defs/predicate_expression"},
        "binding_seal": {"$ref": "#/$defs/binding_seal"},
        "statement_id": {"$ref": "#/$defs/statement_id"},
        "created_at": {"$ref": "#/$defs/rfc3339"},
        "actor": {"$ref": "#/$defs/ref"},
        "truth_status": {"$ref": "#/$defs/truth_status"},
        "provenance": {"$ref": "#/$defs/provenance"},
        "evidence_refs": {"type": "array", "items": {"$ref": "#/$defs/ref"},
                          "uniqueItems": True},
        "cause_refs": {"type": "array", "items": {"$ref": "#/$defs/statement_id"},
                       "uniqueItems": True},
        "supersedes": {"$ref": "#/$defs/statement_id"},
        "literals": {"$ref": "#/$defs/literals"},
    }


_OBSERVED_NEEDS_EVIDENCE = {
    "if": {"properties": {"truth_status": {"const": "observed"}},
           "required": ["truth_status"]},
    "then": {"required": ["evidence_refs"],
             "properties": {"evidence_refs": {"minItems": 1}}},
}

_DESCRIPTIONS = {
    "ParsedStatement": (
        "Syntax-only record: a surface, its tokens and a pin on the parse. It carries no "
        "binding, no truth status and no authorization: a parse-valid line is not a fact "
        "and not a permission (CHANGE_GATES 4, 5)."),
    "BoundStatement": (
        "A parsed statement plus entity binding: resolution_status (independent of the "
        "parse), resolution_context, per-entity bound_ref / candidates and a binding seal "
        "that makes the binding tamper-evident. Truth, actor and provenance are optional "
        "here and mandatory in AgentEvent."),
    "AgentEvent": (
        "A complete persisted agent event: a BoundStatement that also requires "
        "statement_id, created_at (RFC 3339), actor, truth_status and provenance, and "
        "requires evidence_refs whenever truth_status is 'observed'. Nothing in this "
        "profile grants permission to act."),
}


def build_schema(profile: str) -> dict:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile!r}")
    defs = _defs()
    props = {"profile": {"const": profile}, **_common_props()}
    required = ["profile", "schema_version", "token_version", "surface", "tokens",
                "parse_reference"]
    all_of = []
    if profile == "ParsedStatement":
        props["statement_id"] = {"$ref": "#/$defs/statement_id"}
    else:
        props.update(_bound_props())
        required += ["resolution_status", "resolution_context", "binding_seal"]
        all_of.append(_OBSERVED_NEEDS_EVIDENCE)
    if profile == "AgentEvent":
        required += ["statement_id", "created_at", "actor", "truth_status", "provenance"]
        props["resolution_context"] = {**props["resolution_context"], "minItems": 1}
    schema = {
        "$schema": DRAFT,
        "$id": ID_BASE + FILES[profile],
        "title": f"OpenPona {profile} (record profile {SCHEMA_VERSION})",
        "description": _DESCRIPTIONS[profile],
        "$defs": defs,
    }
    schema.update(_strict(props, required, **({"allOf": all_of} if all_of else {})))
    return schema


def build_schemas() -> dict[str, dict]:
    return {p: build_schema(p) for p in PROFILES}


def dumps(schema: dict) -> str:
    """Stable, human-diffable text of a schema file."""
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def write(directory: str | Path) -> list[Path]:
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for profile, schema in build_schemas().items():
        path = out / FILES[profile]
        path.write_text(dumps(schema), encoding="utf-8")
        paths.append(path)
    return paths


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write":
        for p in write(sys.argv[2]):
            print(p)
    else:
        print("usage: python -m openpona.record_schemas --write <dir>", file=sys.stderr)
        sys.exit(2)
