# Agent event contract and policy gate

Classification: **ENGINEERING** (agent integration protocol). Nothing here changes canon:
no token is added (42 tokens, `anu 1.1`), `grammar.lark` is untouched, and no authority
policy is part of the grammar or of the persisted record profiles. Ticket: TP-11
(depends on TP-01 bounded parsing, TP-03 record profiles). Reference implementation:
`openpona/agent_pipeline.py`; tests: `tests/test_agent_pipeline.py` (in-memory fake runtime,
no subprocess, no network, no file writes).

Every decision marked **PENDING AUTHOR REVIEW** is a proposal, not an author decision.

## Pipeline

```text
agent suggests a structured event
  -> parse            openpona.parse            SYNTAX_INVALID | AMBIGUOUS_PARSE | RESOURCE_EXHAUSTED
  -> bind             injected resolver         BINDING_UNRESOLVED | BINDING_AMBIGUOUS
  -> status/evidence  AgentEvent profile + strict observed rule      RECORD_INVALID
  -> persist valid statement (never before this point)
  -> policy gate      injected policy           POLICY_DENIED     (no effect requested: ACCEPTED)
  -> effect           injected runtime.execute  EXECUTION_FAILED | RESOURCE_EXHAUSTED | EXECUTED
  -> fresh observation  runtime.check_world     OBSERVED (else the outcome stays EXECUTED)
```

Plus `ENVELOPE_INVALID` (malformed event or an authority-looking key) and `DUPLICATE`
(idempotency key already processed). The outcome set is the closed enum
`openpona.agent_pipeline.Outcome`; each value is a separate audit entry.

## Rules

1. **A valid statement is not a command.** An effect runs only if the envelope carries an
   explicit `effect` request, every earlier stage passed and the injected policy allows it.
   The default policy denies everything. A policy that raises denies (fail closed).
2. **Authority is outside the language.** The policy receives actor, origin, action, args,
   `truth_status`, surface, bound references and the idempotency key. There is no
   `authorized` field in the envelope, the policy request or the record; envelope keys that
   look like authority (`authorized`, `policy`, `permitted`, `sudo`, ...) are rejected, never honoured.
3. **`requested` / `intended` are claims.** They never imply authorization; the same event
   with any `truth_status` gets the same gate verdict.
4. **Untrusted origin cannot request effects.** `origin: "untrusted"` (user text, tool
   output, web content) is denied before the policy is asked. Such an event may still be
   stored as a statement if it is valid.
5. **Exit 0 is not an observation.** `EXECUTED` means the runtime returned 0. `OBSERVED`
   needs a separate `check_world` call that returns `confirmed` and an evidence reference the
   runtime itself can verify. Otherwise the outcome stays `EXECUTED`.
6. **Strict profile: `observed` needs check-world evidence.** An agent statement with
   `truth_status: observed` is rejected (`RECORD_INVALID`) unless every `evidence_refs`
   entry is verified by `runtime.verify_evidence`. The lenient profile only applies the
   AgentEvent rule (non-empty `evidence_refs`).
7. **Validate before persistence.** The record is built, sealed (TP-03) and validated as an
   `AgentEvent` before it is stored. Invalid, unbound and ambiguous statements are audited but not persisted.
8. **No guessing.** Parse ambiguity and address ambiguity are values: no reading and no
   candidate is picked.

## Event envelope

```json
{
  "event_id": "ev-1",
  "idempotency_key": "slack:1700000000.001:rerun",
  "origin": "agent",
  "actor": "urn:agent:linja",
  "surface": "ma pali la ilo pali li pona ala",
  "truth_status": "intended",
  "created_at": "2026-10-08T09:00:00Z",
  "resolution_context": ["project:acme-web", "repo:acme-web"],
  "evidence_refs": [],
  "literals": {"pr_number": 678},
  "source_event": "slack:1700000000.001",
  "effect": {"action": "rerun_ci", "args": {"pr": 678}}
}
```

Required: `event_id`, `idempotency_key`, `origin` (`agent` | `human` | `untrusted`), `actor`,
`surface`, `truth_status`, `created_at`. `effect` is optional and separate from the
statement; it is a request, not a permission. Unknown keys are rejected.

### Structured agent output

The agent returns the envelope fields (at least `surface` and `truth_status`, optionally
`effect`, `evidence_refs`, `literals`) as one JSON object, not a `surface | status` string
to be stripped afterwards. `AgentPipeline.suggest` fills `event_id`, `idempotency_key`,
`origin`, `actor`, `created_at` and `resolution_context` from the integration context;
the key is derived from the source event and the suggestion, so replaying one source event
cannot execute twice. Identity and provenance fields (`origin`, `actor`, `event_id`,
`idempotency_key`, `source_event`, `created_at`) are caller-owned: `suggest` assigns them
unconditionally, and agent output that contains any of them is rejected as
`ENVELOPE_INVALID` (`AGENT_FORBIDDEN_FIELDS`). Prompt: `prompts/openpona_system_structured.md`.

### Human one-line view

`surface | status` (`prompts/openpona_system.md`) stays a view of the same data:
`to_line_view` and `from_line_view` convert. The status is never part of the surface (the
parser rejects it); `suggest` accepts a legacy line from an agent and treats it as the same
structured suggestion (no `effect`, so it can never execute).

## Idempotency, replay, audit

* The first event with an `idempotency_key` is processed; the same key again returns
  `DUPLICATE` with `original_outcome`, never runs `execute` again, and the key is passed to
  `runtime.execute` so a runtime can deduplicate as well.
* The same key with a different payload is also `DUPLICATE` (audit flags
  `identical_payload: false`); it is never executed.
* The audit log is append-only and hash-chained (`prev_hash`, `hash`); `entries` returns
  copies, `verify_chain()` detects edits. It records every stage outcome, including denials
  and duplicates. Persisted records are never edited; a changed binding is a new record that
  supersedes the old one (`docs/record-profiles.md`).
* The in-memory store and log are the reference; durable storage, signing and retention are
  out of scope (**PENDING AUTHOR REVIEW**).

## Injected interfaces

| Interface | Shape |
|---|---|
| resolver | `resolver(role, tokens, resolution_context) -> list[str]`; 0 candidates unresolved, 1 bound, more ambiguous |
| policy | `decide(PolicyRequest) -> PolicyDecision(allow, reason)` |
| runtime | `execute(action, args, idempotency_key) -> ExecResult`, `check_world(action, args, bindings) -> Observation(confirmed, evidence_ref)`, `verify_evidence(ref) -> bool` |

## Limits (not proved)

* Tested only against the in-memory `FakeRuntime`; no real runtime, no concurrency (the
  reference store is not thread-safe, a real one needs an atomic check-and-set on the key).
* The authority-key scan is a name heuristic, a backstop; the gate is the control.
* `OBSERVED` re-uses the statement surface with `truth_status: observed` and the runtime as
  actor; whether the observation should carry its own surface is **PENDING AUTHOR REVIEW**.
