# Record profiles: ParsedStatement, BoundStatement, AgentEvent

Classification: **ENGINEERING** (persisted-record interface). Nothing here changes canon:
no token is added (the inventory stays the 42 tokens of `anu 1.1`), the grammar and the
96 baseline conformance outcomes are unchanged, and `canon/`, `SPEC.md` and
`data/matrix.csv` are not touched.

Ticket: TP-03 (OpenPona Improvement TZ v0.2). Depends on TP-02 (typed AST, parser API 1.0.0).
Status of every decision on this page: a proposal for the author. Items that need an
author decision are marked **PENDING AUTHOR REVIEW** and collected at the end.

## Why profiles

`schema/statement.schema.json` (legacy) describes one object that mixes four different
things: what the sentence says (syntax), what its addresses refer to (binding), what the
speaker claims about it (truth status) and who recorded it (provenance). The records that
`docs/for-agents.md` section 6 recommends to agents carry more than that schema allows
(`resolution_context`, `resolution_status`, `candidates`, `evidence`) and the schema
required almost none of the fields a persisted event needs. TP-03 splits the record into
three profiles that build on each other:

| Profile | Schema file | Carries | Typical use |
|---|---|---|---|
| `ParsedStatement` | `schema/profiles/parsed_statement.schema.json` | surface, tokens, a pin on the parse | caching or exchanging a syntax result |
| `BoundStatement` | `schema/profiles/bound_statement.schema.json` | + `resolution_status`, `resolution_context`, per-entity `bound_ref` / `candidates`, `binding_seal`; truth, actor and provenance optional | a statement with its addresses bound (or honestly left ambiguous) |
| `AgentEvent` | `schema/profiles/agent_event.schema.json` | + required `statement_id`, `created_at`, `actor`, `truth_status`, `provenance` | a complete persisted event |

A record names its profile in the `profile` field. The language itself stays independent of
the runtime: these are storage profiles, not grammar.

## Four identifiers, four meanings

| Identifier | Value | What it versions |
|---|---|---|
| Token inventory | `anu 1.1` | the 42 tokens and their arrangement (`token_version` in every record) |
| Package | `0.2.0` | the distributed corpus and reference parser |
| Parser API | `1.0.0` | the shape of `ParseResult` and the AST JSON (`parse_reference.api_version`) |
| **Record profiles** | `records-1.0.0` | the shape of these three schemas (`schema_version`) |

They move independently; none implies another. The value `records-1.0.0` and the bump
rule (a field added, removed or retyped bumps the identifier) are a proposal, **PENDING
AUTHOR REVIEW**.

## Fields

Required fields per profile (`R` required, `o` optional, `-` not allowed). Any key not
listed here is rejected unless it is an `x-` extension key (see below).

| Field | Parsed | Bound | AgentEvent | Meaning |
|---|---|---|---|---|
| `profile` | R | R | R | one of the three profile names |
| `schema_version` | R | R | R | `records-1.0.0` |
| `token_version` | R | R | R | `anu 1.1` |
| `surface` | R | R | R | the one-line statement, the 42 tokens separated by single spaces |
| `tokens` | R | R | R | the surface split into tokens; every item is one of the 42 tokens |
| `parse_reference` | R | R | R | pin on the parse (below) |
| `statement_id` | o | o | R | stable id, `[A-Za-z0-9][A-Za-z0-9:._/-]*` |
| `resolution_status` | - | R | R | `RESOLVED`, `AMBIGUOUS` or `UNRESOLVED` (independent of the parse) |
| `resolution_context` | - | R | R (at least 1) | context stack the addresses were resolved in, narrowest first |
| `subject`, `object`, `context` | - | o | o | entity bindings (below) |
| `predicate` | - | o | o | `{tokens}` only; a predicate is not an entity and is never bound |
| `binding_seal` | - | R | R | tamper-evident seal over the binding (below) |
| `created_at` | - | o | R | RFC 3339 date-time with offset |
| `actor` | - | o | R | reference of the author of the statement (`urn:agent:linja`) |
| `truth_status` | - | o | R | `observed`, `asserted`, `requested`, `intended`, `hypothesis`, `inferred`, `unknown`, `rejected` |
| `provenance` | - | o | R | `{kind, source_event?}` |
| `evidence_refs` | - | o | o, but R and non-empty when `truth_status` is `observed` | what was checked |
| `cause_refs` | - | o | o | `statement_id`s this record follows from |
| `supersedes` | - | o | o | `statement_id` of the record this one replaces (new binding) |
| `literals` | - | o | o | external values (numbers, ids, strings); free-form map of scalars |

### parse_reference

```json
{"api_version": "1.0.0", "status": "RESOLVED", "alternative_index": 0, "ast_sha256": "<64 hex>"}
```

`status` is the SYNTAX status (`RESOLVED` or `AMBIGUOUS`); `INVALID` and
`RESOURCE_EXHAUSTED` parses are never persisted as statements. `alternative_index` selects
one of the parse alternatives of `openpona.parse(surface).alternatives`, `ast_sha256` is the
sha256 of that alternative's canonical JSON (`openpona.ast.to_canonical_json`, spans
included). `UNRESOLVED` and entity candidates are not parse results; they live in
`resolution_status` and the entity objects. Syntax status and binding status are two
fields, so a record can be `parse_reference.status = RESOLVED` and `resolution_status =
UNRESOLVED` at once (the example `bound_statement_unresolved_question.json`).

### Entity binding (`subject`, `object`, `context`)

```json
{"tokens": ["ilo", "pali"], "resolution_status": "RESOLVED", "bound_ref": "ci:run-4711"}
{"tokens": ["ilo", "pali"], "resolution_status": "AMBIGUOUS",
 "candidates": ["ci:build-service", "ci:lint-service"]}
```

| Entity `resolution_status` | `bound_ref` | `candidates` |
|---|---|---|
| `RESOLVED` | required, one reference | absent, or exactly `[bound_ref]` |
| `AMBIGUOUS` | null or absent (never pick one) | at least 2 |
| `UNRESOLVED` | null or absent | empty or absent |

This is `canon/05_addressing.md` (zero candidates `UNRESOLVED`, several `AMBIGUOUS`, "no
probabilistic guess may silently become a historical binding") written as a rule.
`tokens` of an entity is the token list of the AST node in that role; the validator
checks it against the parse and does not trust it. The statement-level `resolution_status`
must equal the aggregate of the entities present: `AMBIGUOUS` if any entity is, else
`UNRESOLVED` if any is, else `RESOLVED` (**PENDING AUTHOR REVIEW**).

AST roles used for the check (`openpona.binding.ast_roles`): `context` is the clause before
a plain `la` (a source context `tan X la` is not a resolution context); `subject` is the
subject of a predication; `object` is any `e` item of any predicate; `predicate` is any
predicate head. When the AST has a subject or a `la` context the record must bind it
(typed `missing_binding` otherwise), so a record cannot silently skip an address
(**PENDING AUTHOR REVIEW**). Objects are optional: `kama pona` in `jan li wile e kama pona`
is a state, not an entity.

### binding_seal and immutability

```json
{"algorithm": "sha256", "source_revision": "graph-rev:acme-web@2026-10-08", "digest": "<64 hex>"}
```

`source_revision` names the revision of the graph or ontology the addresses were resolved
against. `digest` is the sha256 of the canonical JSON (sorted keys, no whitespace) of:
`statement_id`, `token_version`, `surface`, `parse_reference`, `resolution_status`,
`resolution_context`, the entity and predicate objects, and `source_revision`
(`openpona.binding.binding_digest`). It does **not** cover truth status, actor, evidence,
literals or `x-` keys. Consequences:

* Editing a persisted binding in place (a `bound_ref`, the `resolution_context`, the
  surface) makes the digest wrong: `binding_seal_mismatch`.
* Recomputing the digest after the edit passes the single-record check, which is why
  persisted history is also compared: `openpona.binding.check_immutable(old, new)` (CLI:
  `validate-record <file> --persisted <earlier file>`) reports `bound_ref_rewritten`,
  `resolution_context_rewritten`, `binding_seal_rewritten` or `persisted_record_modified`
  for any difference outside `x-` keys between two versions of one `statement_id`.
* A later context may resolve the same address differently NOW. The way to say so is a
  NEW record: new `statement_id`, `supersedes` = the old id, a new seal. The old record
  stays byte-for-byte as written (`canon/05`: "must not change what the historical
  statement referred to").

The seal is tamper-evidence against accidents and silent edits, not authentication: anyone
who can write the store can write a new digest. Signing is out of scope.

### Provenance and evidence

`provenance.kind` is one of `source_event` (requires `source_event`, the id of the event it
derives from), `runtime_observation`, `agent_statement`, `human_statement`,
`legacy_migration` (**PENDING AUTHOR REVIEW**: the list). An AgentEvent always has a
provenance. Evidence is optional in general (`evidence_refs`), and mandatory for exactly one
claim: `truth_status: observed` requires at least one `evidence_refs` entry
(`observed_without_evidence` otherwise). `requested`, `intended` and `observed` are three
values of the required `truth_status` field; they are distinguishable without reading the
surface tokens (the H-TS `lukin la` / `wile la` prefixes remain a research convention and
are not read by the validator).

## Strictness and the `x-` extension namespace

Every object in the three profiles (the record, `parse_reference`, entities, `predicate`,
`binding_seal`, `provenance`) rejects unknown keys (`unknown_key`) **except** keys matching
`^x-[A-Za-z0-9][A-Za-z0-9._-]*$`. The `x-` namespace is the only extension point:

* extension values may be any JSON;
* extension keys are ignored by the validator, are not covered by the seal and are not
  compared by `check_immutable`, so they may be added to a persisted record;
* extensions must not change the meaning of the binding, and must not carry an
  authorization (the validator rejects a key named like one, below);
* the two examples in `examples/records/valid/` use `x-note`; the migration helper uses
  `x-legacy` and `x-migration`.

The only free-form object is `literals`, a map of scalar values.

## What the schema cannot check, and what checks it

JSON Schema (2020-12) validates shape. The binding validator (`openpona/binding.py`)
adds the cross-checks. The schema files are generated by `openpona/record_schemas.py`
from the packaged token table so the 42-token enum is never typed by hand; a test compares
it with `data/matrix.csv` and checks the committed files equal the generator output.

```text
python -m openpona validate-record <file.json>                 exit 0 valid, 1 invalid
python -m openpona validate-record <new.json> --persisted <old.json>   also check immutability
python -m openpona.record_schemas --write schema/profiles      regenerate the schema files
```

The checker is standard library only (`openpona/_schemacheck.py`, a deliberate subset of
2020-12; it raises on any keyword it does not implement). The schema files are ordinary
2020-12 schemas, so a full validator such as `jsonschema` accepts them too; no dependency
on it is added. Input is JSON; YAML is not read.

Typed reasons (`validate-record` prints the first as `invalid: <code>` and then every
finding; a code is stable API, the message is not):

| Code | Stage | Meaning |
|---|---|---|
| `unreadable_file`, `invalid_json`, `not_an_object` | input | the file is not a JSON object |
| `missing_profile`, `unknown_profile`, `profile_mismatch` | input | `profile` absent, not one of the three, or not the one asked for |
| `authorization_from_truth_status` | structure | a key such as `authorized`, `authorization`, `permitted`, `may_execute` (also as `x-...`) anywhere outside `literals` |
| `missing_required_field` | schema | a required field is absent |
| `unknown_key` | schema | a key that is neither documented nor `x-` |
| `non_canonical_token` | schema | an item of a `tokens` array is not one of the 42 tokens |
| `token_version_mismatch`, `schema_version_unsupported` | schema | `token_version` is not `anu 1.1`, `schema_version` is not `records-1.0.0` |
| `wrong_type`, `bad_format`, `bad_timestamp`, `invalid_value`, `constraint_violation` | schema | type, pattern, RFC 3339, enum or size violation |
| `observed_without_evidence` | schema rule | `observed` with no `evidence_refs` |
| `provenance_source_missing` | schema rule | `provenance.kind` `source_event` without `source_event` |
| `binding_rule_violation` | schema rule | an entity-status rule not already reported as a typed binding code |
| `surface_tokens_mismatch` | parser | `surface` is not the single-space join of `tokens` |
| `surface_parse_invalid`, `surface_parse_unavailable` | parser | the reference parser answers `INVALID`, or gives no verdict (`RESOURCE_EXHAUSTED`) |
| `parse_api_incompatible` | parser | the record pins another major parser API version |
| `parse_reference_mismatch` | parser | pinned status, alternative index or AST digest differs from the parse |
| `ast_subject_mismatch`, `ast_object_mismatch`, `ast_context_mismatch`, `ast_predicate_mismatch` | AST | a role's tokens differ from the AST node in that role |
| `missing_binding` | AST | the AST has a subject or a `la` context and the record binds none |
| `unbound_ambiguous_address` | binding | an address with 2 or more candidates and no `bound_ref` is claimed `RESOLVED` (entity or statement) |
| `missing_bound_ref` | binding | `RESOLVED` entity without `bound_ref` and without candidates |
| `ambiguous_address_bound` | binding | `AMBIGUOUS` entity that nevertheless carries a `bound_ref` |
| `conflicting_bound_ref` | binding | one address bound to two references, or a `bound_ref` that competes with other candidates |
| `resolution_status_mismatch` | binding | statement status is not the aggregate of the entities |
| `binding_seal_mismatch` | seal | the sealed content changed after sealing |
| `statement_id_mismatch`, `bound_ref_rewritten`, `resolution_context_rewritten`, `binding_seal_rewritten`, `persisted_record_modified` | immutability | `check_immutable` between two versions of one record |

## Negative guarantees (CHANGE_GATES 4 and 5)

* **Schema-valid is not true.** A valid `observed` event with evidence references is a
  well-formed claim; the validator does not open the evidence.
* **Parse-valid is not bound.** A line the parser accepts can still carry two different
  `bound_ref`s for one address (`conflicting_bound_ref`) or a bound ambiguous address, and
  is then not accepted as a bound event.
* **Truth is not permission.** There is no authorization field in any profile, and a key
  that looks like one is rejected with `authorization_from_truth_status`. A `requested`
  event authorizes nothing, an `intended` event is not an executed act, and an `observed`
  event is not authority. Identity, policy and preconditions are enforced by the runtime
  outside the language. The key-name check is a heuristic: it catches the obvious
  derivation, it cannot prove that no runtime reads meaning into an arbitrary field.

## Examples

`examples/records/valid/` (all validate; every file is JSON):

| File | Profile | Shows |
|---|---|---|
| `agent_event_ci_story_1_observed_red.json` ... `_7_observed_green.json` | AgentEvent | the seven statements of `examples/walkthrough_ci_failure.md` ("The whole story in order") as fully bound events: observed, requested, intended, intended, observed, intended, observed |
| `bound_statement_ambiguous_ci_tool.json` | BoundStatement | two matching CI tools: both candidates kept, nothing bound |
| `bound_statement_unresolved_question.json` | BoundStatement | `seme` stays `UNRESOLVED`; parse status and binding status differ |
| `parsed_statement.json`, `parsed_statement_ambiguous_reading.json` | ParsedStatement | syntax only; the second pins reading 1 of an ambiguous parse |

`examples/records/invalid/` (each fails with exactly its own typed reason; the file name is
the code, except where noted):

| File | Primary reason |
|---|---|
| `conflicting_bound_ref.json` | `conflicting_bound_ref`: `ilo pali` bound to two references in one context |
| `missing_critical_field.json` | `missing_required_field`: no `created_at` |
| `unknown_key.json` | `unknown_key`: `severity` |
| `ast_subject_mismatch.json` | `ast_subject_mismatch`: sidecar says `jan linja`, the AST subject is `ilo pali` |
| `unbound_ambiguous_address.json` | `unbound_ambiguous_address` |
| `non_canonical_token.json` | `non_canonical_token`: `sin` |
| `authorization_from_truth_status.json` | `authorization_from_truth_status` |

Every example carries an `x-note` or `x-defect` explaining it. All identifiers
(`acme-web`, `ci:run-4711`, times, the revision) are invented; the examples are
illustrations, not data.

Numbering note: the walkthrough's status table (Step 4) numbers five of the seven
statements differently from its closing block. The example files follow the closing block.
Statement 4 (`jan linja li pali e nasin pona`) is recorded `intended`: the act itself is
executed by the runtime, which is outside the language, and what the agent observes
afterwards is statement 5. Statement 6 is recorded `intended` for the same reason.

## What is not claimed

* The seal, the aggregate rule, the mandatory subject/context binding and the provenance
  kinds are engineering proposals, not language rules.
* No record format is canon. `canon/05_addressing.md` fixes the model (stable reference
  plus address plus resolution context); the field names here are an implementation.
* The legacy `schema/statement.schema.json` is not edited. Its `parse_status` enum still
  lists `UNRESOLVED`; migration to the split is in `docs/record-migration.md`.

## Pending author review

1. The identifier `records-1.0.0` and its bump rule.
2. The statement-level `resolution_status` as the aggregate of the entity statuses.
3. Mandatory binding of the AST subject and `la` context.
4. The list of `provenance.kind` values, and requiring a provenance in every AgentEvent.
5. The seal payload (what is covered) and `source_revision` as its required anchor.
6. Whether `observed` is the only truth status that needs evidence (as proposed), or
   `asserted` and `inferred` too.
7. Retiring the legacy `parse_status` field in favour of `parse_reference.status` and
   `resolution_status` (see the migration document).
8. The `authorization_from_truth_status` key-name list.
