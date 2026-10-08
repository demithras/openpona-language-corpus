"""Agent production pipeline and policy gate (TP-11).  ENGINEERING module.

    suggest -> parse -> bind -> status/evidence validation -> policy gate
            -> optional effect (injected runtime) -> fresh observation

A valid OpenPona statement is data.  It never executes anything: an effect happens
only when (1) the envelope carries an explicit `effect` request next to the statement,
(2) every earlier stage passed and (3) the injected policy returns allow.  Authority is
a runtime concern (CHANGE_GATES 4); it is NOT part of the grammar, the token set or the
persisted record.  `truth_status` values `requested` / `intended` are claims, not
permissions, and a runtime that reports exit code 0 has not shown the world changed:
`OBSERVED` needs a fresh `check_world` observation that carries evidence.

The module does no I/O of its own: parser, resolver, policy, runtime and clock are
injected or pure.  Contract: docs/agent-event-contract.md.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy
import enum
import hashlib
import json
from typing import Any, Callable, Optional, Protocol

from . import parse
from . import binding as _binding
from .parser import Budget

__all__ = [
    "Outcome", "PipelineResult", "PolicyRequest", "PolicyDecision", "ExecResult",
    "Observation", "Runtime", "AuditLog", "AgentPipeline", "DenyAllPolicy",
    "ResourceExhaustedError", "envelope_digest", "to_line_view", "from_line_view",
    "ENVELOPE_KEYS", "ORIGINS", "STRICT", "LENIENT",
]


class Outcome(str, enum.Enum):
    """Closed set of pipeline outcomes.  Each is a distinct, auditable verdict."""
    ENVELOPE_INVALID = "ENVELOPE_INVALID"      # malformed event / smuggled authority key
    SYNTAX_INVALID = "SYNTAX_INVALID"          # parser said INVALID
    AMBIGUOUS_PARSE = "AMBIGUOUS_PARSE"        # parser said AMBIGUOUS; no reading is picked
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"  # parse budget or runtime quota ran out
    BINDING_UNRESOLVED = "BINDING_UNRESOLVED"  # an address has no candidate
    BINDING_AMBIGUOUS = "BINDING_AMBIGUOUS"    # an address has several candidates
    RECORD_INVALID = "RECORD_INVALID"          # status / evidence / profile validation failed
    POLICY_DENIED = "POLICY_DENIED"            # gate said no (or origin untrusted)
    ACCEPTED = "ACCEPTED"                      # valid statement persisted, no effect requested
    EXECUTION_FAILED = "EXECUTION_FAILED"      # runtime raised or returned non-zero
    EXECUTED = "EXECUTED"                      # runtime returned 0; world state NOT verified
    OBSERVED = "OBSERVED"                      # fresh check_world observation with evidence
    DUPLICATE = "DUPLICATE"                    # idempotency key already processed


ORIGINS = ("agent", "human", "untrusted")  # untrusted = user content, tool output, web text
STRICT, LENIENT = "strict", "lenient"
ENVELOPE_KEYS = frozenset({
    "event_id", "idempotency_key", "origin", "actor", "surface", "truth_status",
    "created_at", "resolution_context", "evidence_refs", "literals", "effect",
    "source_event"})
_STATUSES = ("observed", "asserted", "requested", "intended", "hypothesis", "inferred",
             "unknown", "rejected")
_AUTH_WORDS = ("authoriz", "authoris", "permit", "may_execute", "allowed", "policy",
               "approved", "grant", "sudo", "override")


class ResourceExhaustedError(Exception):
    """Raised by a runtime whose quota ran out."""


@dataclass(frozen=True)
class PolicyRequest:
    """What the gate sees.  There is deliberately no `authorized` field here."""
    actor: str
    origin: str
    action: str
    args: dict
    truth_status: str
    surface: str
    bindings: dict          # role -> bound_ref (objects -> list)
    idempotency_key: str


@dataclass(frozen=True)
class PolicyDecision:
    allow: bool
    reason: str


class DenyAllPolicy:
    """Default gate: nothing is authorized until an operator injects a policy."""
    def decide(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(False, "default deny: no policy injected")


@dataclass(frozen=True)
class ExecResult:
    exit_code: int
    detail: str = ""


@dataclass(frozen=True)
class Observation:
    confirmed: bool
    evidence_ref: Optional[str] = None


class Runtime(Protocol):
    def execute(self, action: str, args: dict, idempotency_key: str) -> ExecResult: ...
    def check_world(self, action: str, args: dict, bindings: dict) -> Observation: ...
    def verify_evidence(self, ref: str) -> bool: ...


@dataclass(frozen=True)
class PipelineResult:
    outcome: Outcome
    event_id: str
    idempotency_key: str
    detail: str = ""
    issues: tuple = ()
    record: Optional[dict] = None
    original_outcome: Optional[Outcome] = None   # set on DUPLICATE
    policy_allowed: bool = False
    executed: bool = False


# --------------------------------------------------------------- append-only audit
class AuditLog:
    """Append-only list of hash-chained entries.  Entries are never edited; `entries`
    returns deep copies so callers cannot mutate history."""
    def __init__(self):
        self._entries: list[dict] = []

    def append(self, event_id: str, key: str, stage: str, outcome: str, detail: str = "",
               **extra) -> dict:
        prev = self._entries[-1]["hash"] if self._entries else "0" * 64
        entry = {"seq": len(self._entries), "event_id": event_id, "idempotency_key": key,
                 "stage": stage, "outcome": outcome, "detail": detail, "extra": extra,
                 "prev_hash": prev}
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True, default=str).encode()).hexdigest()
        self._entries.append(entry)
        return copy.deepcopy(entry)

    @property
    def entries(self) -> tuple:
        return tuple(copy.deepcopy(self._entries))

    def __len__(self):
        return len(self._entries)

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for e in self._entries:
            body = {k: v for k, v in e.items() if k != "hash"}
            if e["prev_hash"] != prev or e["hash"] != hashlib.sha256(
                    json.dumps(body, sort_keys=True, default=str).encode()).hexdigest():
                return False
            prev = e["hash"]
        return True


def envelope_digest(env: dict) -> str:
    return hashlib.sha256(json.dumps(env, sort_keys=True, default=str,
                                     ensure_ascii=False).encode()).hexdigest()


# ------------------------------------------------------- human one-line view (compat)
def to_line_view(surface: str, truth_status: str) -> str:
    """The human `surface | status` line of prompts/openpona_system.md."""
    return f"{surface} | {truth_status}"


def from_line_view(line: str) -> dict:
    """Split a legacy line into the structured fields.  The status is NOT part of the
    surface (the parser rejects it); a line without ` | ` yields truth_status None."""
    if " | " in line:
        surface, status = line.rsplit(" | ", 1)
        return {"surface": surface.strip(), "truth_status": status.strip().split()[0]}
    return {"surface": line.strip(), "truth_status": None}


def _auth_like(key: str) -> bool:
    k = str(key).lower()
    return any(w in k for w in _AUTH_WORDS)


def _scan_authority(obj, path="") -> Optional[str]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if _auth_like(k):
                return f"{path}/{k}"
            hit = _scan_authority(v, f"{path}/{k}")
            if hit:
                return hit
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hit = _scan_authority(v, f"{path}/{i}")
            if hit:
                return hit
    return None


# -------------------------------------------------------------------- the pipeline
class AgentPipeline:
    """One pipeline instance = one store + one audit log.

    resolver(role, tokens, resolution_context) -> list of candidate refs
    policy.decide(PolicyRequest) -> PolicyDecision
    runtime: see `Runtime`.  clock is not needed: `created_at` comes from the envelope.
    """

    def __init__(self, resolver: Callable[[str, list, list], list], runtime: Runtime,
                 policy=None, profile: str = STRICT, source_revision: str = "graph-rev:unset",
                 budget: Optional[Budget] = None):
        if profile not in (STRICT, LENIENT):
            raise ValueError("profile must be 'strict' or 'lenient'")
        self.resolver, self.runtime = resolver, runtime
        self.policy = policy if policy is not None else DenyAllPolicy()
        self.profile, self.source_revision, self.budget = profile, source_revision, budget
        self.audit = AuditLog()
        self._records: list[dict] = []          # persisted, validated records (append-only)
        self._seen: dict[str, tuple[str, PipelineResult]] = {}

    @property
    def records(self) -> tuple:
        return tuple(copy.deepcopy(self._records))

    # ---- stage 0: suggest ------------------------------------------------------
    def suggest(self, agent: Callable[[dict], Any], context: dict, *, source_event: str,
                origin: str = "agent", actor: str = "urn:agent:unknown",
                created_at: str = "1970-01-01T00:00:00Z") -> PipelineResult:
        """Ask `agent(context)` for a structured suggestion and run it through `submit`.
        The agent may return a dict with the envelope fields or a legacy string line
        (`surface | status`).  The idempotency key is derived from the source event and
        the suggestion, so replaying the same source event never executes twice."""
        out = agent(copy.deepcopy(context))
        if isinstance(out, str):
            out = from_line_view(out)
        if not isinstance(out, dict):
            return self._reject(f"{source_event}:bad-suggestion", f"{source_event}:bad",
                                Outcome.ENVELOPE_INVALID, "suggestion is neither dict nor line")
        env = {k: v for k, v in out.items() if k in ENVELOPE_KEYS}
        extra = {k: v for k, v in out.items() if k not in ENVELOPE_KEYS}
        if extra:
            env["_unknown"] = extra            # forces ENVELOPE_INVALID, never silently dropped
        digest = hashlib.sha256(json.dumps(out, sort_keys=True, default=str).encode()).hexdigest()[:16]
        env.setdefault("event_id", f"{source_event}:{digest}")
        env.setdefault("idempotency_key", f"{source_event}:{digest}")
        env.setdefault("origin", origin)
        env.setdefault("actor", actor)
        env.setdefault("created_at", created_at)
        env.setdefault("source_event", source_event)
        env.setdefault("resolution_context", list(context.get("resolution_context", [])))
        return self.submit(env)

    # ---- stages 1..7 -----------------------------------------------------------
    def submit(self, env: dict) -> PipelineResult:
        if not isinstance(env, dict):
            return self._reject("?", "?", Outcome.ENVELOPE_INVALID, "envelope is not an object")
        event_id = str(env.get("event_id", "?"))
        key = env.get("idempotency_key")
        if not isinstance(key, str) or not key:
            return self._reject(event_id, "?", Outcome.ENVELOPE_INVALID,
                                "idempotency_key is required")
        digest = envelope_digest(env)
        if key in self._seen:
            old_digest, old = self._seen[key]
            same = old_digest == digest
            self.audit.append(event_id, key, "idempotency", Outcome.DUPLICATE.value,
                              "replay of an identical event" if same else
                              "same idempotency_key, different payload: not executed",
                              original=old.outcome.value, identical_payload=same)
            return PipelineResult(Outcome.DUPLICATE, event_id, key,
                                  "replay" if same else "key reused with a different payload",
                                  original_outcome=old.outcome)
        res = self._run(env, event_id, key)
        self._seen[key] = (digest, res)
        return res

    def _finish(self, stage, event_id, key, outcome, detail="", issues=(), record=None, **kw):
        self.audit.append(event_id, key, stage, outcome.value, detail,
                          issues=[getattr(i, "code", str(i)) for i in issues])
        return PipelineResult(outcome, event_id, key, detail, tuple(issues), record, **kw)

    def _reject(self, event_id, key, outcome, detail):
        return self._finish("envelope", event_id, key, outcome, detail)

    def _run(self, env: dict, event_id: str, key: str) -> PipelineResult:
        # envelope shape; authority-looking keys are rejected, never honoured
        unknown = sorted(set(env) - ENVELOPE_KEYS)
        if unknown:
            return self._reject(event_id, key, Outcome.ENVELOPE_INVALID,
                                f"unknown envelope keys: {unknown}")
        hit = _scan_authority({k: v for k, v in env.items() if k not in ("surface",)})
        if hit:
            return self._reject(event_id, key, Outcome.ENVELOPE_INVALID,
                                f"authority-like key at {hit}: authority is not an event field")
        for req in ("event_id", "origin", "actor", "surface", "truth_status", "created_at"):
            if not isinstance(env.get(req), str) or not env[req]:
                return self._reject(event_id, key, Outcome.ENVELOPE_INVALID, f"{req} is required")
        if env["origin"] not in ORIGINS:
            return self._reject(event_id, key, Outcome.ENVELOPE_INVALID, "unknown origin")
        if env["truth_status"] not in _STATUSES:
            return self._reject(event_id, key, Outcome.RECORD_INVALID,
                                f"truth_status {env['truth_status']!r} is not one of the 8")
        effect = env.get("effect")
        if effect is not None and not (isinstance(effect, dict) and isinstance(effect.get("action"), str)
                                       and isinstance(effect.get("args", {}), dict)):
            return self._reject(event_id, key, Outcome.ENVELOPE_INVALID,
                                "effect must be {action: str, args?: object}")

        # parse
        try:
            res = parse(env["surface"], self.budget) if self.budget else parse(env["surface"])
        except Exception as exc:                                     # pragma: no cover
            return self._finish("parse", event_id, key, Outcome.SYNTAX_INVALID, repr(exc))
        if res.status == "RESOURCE_EXHAUSTED":
            return self._finish("parse", event_id, key, Outcome.RESOURCE_EXHAUSTED,
                                res.reason or "parse budget")
        if res.status == "INVALID":
            return self._finish("parse", event_id, key, Outcome.SYNTAX_INVALID,
                                "; ".join(res.errors)[:300])
        if res.status == "AMBIGUOUS":
            return self._finish("parse", event_id, key, Outcome.AMBIGUOUS_PARSE,
                                f"{len(res.alternatives)} readings; none is picked")
        alt = res.alternatives[0]

        # bind (N3): resolver proposes, the pipeline never guesses
        ctx_refs = list(env.get("resolution_context") or [])
        roles = _binding.ast_roles(alt)
        ents: dict = {}
        obj_refs: list = []
        worst = None
        for role, toks in (("context", roles["context"]), ("subject", roles["subject"])):
            if toks is not None:
                ents[role], worst = self._bind(role, toks, ctx_refs, worst)
        bound_objs = []
        for toks in roles["objects"]:
            e, worst = self._bind("object", toks, ctx_refs, worst)
            bound_objs.append(e)
        if worst is not None:
            return self._finish("bind", event_id, key, worst,
                                "; ".join(f"{r}:{e['resolution_status']}" for r, e in ents.items()
                                          if e["resolution_status"] != "RESOLVED"))
        if len(bound_objs) == 1:
            ents["object"] = bound_objs[0]
        obj_refs = [e["bound_ref"] for e in bound_objs]
        statuses = {e["resolution_status"] for e in ents.values()}
        record = {
            "profile": "AgentEvent", "schema_version": "records-1.0.0", "token_version": "anu 1.1",
            "surface": env["surface"], "tokens": list(res.tokens),
            "parse_reference": _binding.parse_reference_for(env["surface"]),
            "statement_id": env["event_id"], "created_at": env["created_at"],
            "actor": env["actor"], "truth_status": env["truth_status"],
            "resolution_status": "RESOLVED", "resolution_context": ctx_refs,
            "provenance": ({"kind": "source_event", "source_event": env["source_event"]}
                           if env.get("source_event") else
                           {"kind": "human_statement" if env["origin"] == "human"
                            else "agent_statement"}),
        }
        assert statuses <= {"RESOLVED"}
        record.update(ents)
        if env.get("literals"):
            record["literals"] = env["literals"]
        if env.get("evidence_refs"):
            record["evidence_refs"] = list(env["evidence_refs"])
        if not ctx_refs:
            return self._finish("validate", event_id, key, Outcome.RECORD_INVALID,
                                "resolution_context is empty")
        record = _binding.seal_record(record, self.source_revision)

        # status / evidence validation BEFORE persistence
        vr = _binding.validate_record(record, "AgentEvent")
        if not vr.valid:
            return self._finish("validate", event_id, key, Outcome.RECORD_INVALID,
                                vr.reason or "", vr.issues)
        if env["truth_status"] == "observed":
            ev = list(env.get("evidence_refs") or [])
            bad = [r for r in ev if not self._evidence_ok(r)]
            if self.profile == STRICT and (not ev or bad):
                return self._finish(
                    "validate", event_id, key, Outcome.RECORD_INVALID,
                    "observed requires check-world evidence issued by the runtime"
                    + (f"; unverified: {bad}" if bad else "; none given"))

        # policy gate
        if effect is None:
            self._persist(record)
            return self._finish("persist", event_id, key, Outcome.ACCEPTED,
                                "valid statement stored; no effect requested", record=record)
        bindings = {r: e["bound_ref"] for r, e in ents.items()}
        bindings["objects"] = obj_refs
        if env["origin"] == "untrusted":
            self._persist(record)
            return self._finish("policy", event_id, key, Outcome.POLICY_DENIED,
                                "untrusted origin cannot request effects", record=record)
        req = PolicyRequest(env["actor"], env["origin"], effect["action"],
                            copy.deepcopy(effect.get("args", {})), env["truth_status"],
                            env["surface"], bindings, key)
        try:
            dec = self.policy.decide(req)
        except Exception as exc:
            dec = PolicyDecision(False, f"policy error (fail closed): {exc!r}")
        if dec.allow is not True:
            self._persist(record)
            return self._finish("policy", event_id, key, Outcome.POLICY_DENIED, dec.reason,
                                record=record)
        self.audit.append(event_id, key, "policy", "ALLOWED", dec.reason)

        # effect
        try:
            ex = self.runtime.execute(effect["action"], copy.deepcopy(effect.get("args", {})), key)
        except ResourceExhaustedError as exc:
            self._persist(record)
            return self._finish("effect", event_id, key, Outcome.RESOURCE_EXHAUSTED, str(exc),
                                record=record, policy_allowed=True)
        except Exception as exc:
            self._persist(record)
            return self._finish("effect", event_id, key, Outcome.EXECUTION_FAILED, repr(exc),
                                record=record, policy_allowed=True)
        self._persist(record)
        if ex.exit_code != 0:
            return self._finish("effect", event_id, key, Outcome.EXECUTION_FAILED,
                                f"exit {ex.exit_code}: {ex.detail}", record=record,
                                policy_allowed=True, executed=True)
        self.audit.append(event_id, key, "effect", "EXIT_0",
                          "runtime returned 0; this is not an observation")

        # fresh observation: a separate check_world call, never the exec result
        try:
            ob = self.runtime.check_world(effect["action"], copy.deepcopy(effect.get("args", {})),
                                          bindings)
        except Exception as exc:
            return self._finish("observe", event_id, key, Outcome.EXECUTED,
                                f"check_world failed: {exc!r}", record=record,
                                policy_allowed=True, executed=True)
        if ob.confirmed and ob.evidence_ref and self._evidence_ok(ob.evidence_ref):
            orec = copy.deepcopy(record)
            orec.pop("binding_seal", None)
            orec.update({"statement_id": env["event_id"] + ":obs", "truth_status": "observed",
                         "evidence_refs": [ob.evidence_ref], "cause_refs": [env["event_id"]],
                         "actor": "urn:runtime:observer",
                         "provenance": {"kind": "runtime_observation"}})
            orec = _binding.seal_record(orec, self.source_revision)
            ov = _binding.validate_record(orec, "AgentEvent")
            if ov.valid:
                self._persist(orec)
                return self._finish("observe", event_id, key, Outcome.OBSERVED,
                                    f"evidence {ob.evidence_ref}", record=orec,
                                    policy_allowed=True, executed=True)
            return self._finish("observe", event_id, key, Outcome.EXECUTED,
                                f"observation record invalid: {ov.reason}", ov.issues,
                                record=record, policy_allowed=True, executed=True)
        return self._finish("observe", event_id, key, Outcome.EXECUTED,
                            "no confirmed observation with evidence", record=record,
                            policy_allowed=True, executed=True)

    # ---- helpers ---------------------------------------------------------------
    def _bind(self, role, tokens, ctx_refs, worst):
        try:
            cands = list(self.resolver(role, list(tokens), list(ctx_refs)))
        except Exception:
            cands = []
        if len(cands) == 1:
            ent = {"tokens": list(tokens), "resolution_status": "RESOLVED", "bound_ref": cands[0]}
        elif len(cands) == 0:
            ent = {"tokens": list(tokens), "resolution_status": "UNRESOLVED"}
            worst = worst or Outcome.BINDING_UNRESOLVED
        else:
            ent = {"tokens": list(tokens), "resolution_status": "AMBIGUOUS",
                   "candidates": sorted(cands)}
            worst = Outcome.BINDING_AMBIGUOUS
        return ent, worst

    def _evidence_ok(self, ref: str) -> bool:
        try:
            return bool(self.runtime.verify_evidence(ref))
        except Exception:
            return False

    def _persist(self, record: dict) -> None:
        self._records.append(copy.deepcopy(record))
