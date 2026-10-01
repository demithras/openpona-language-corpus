# Walkthrough: a red CI, a request, a fix, a green CI

One event (anonymised: `acme-web`, PR 678), from the sentence to the record to what a runtime must refuse. Every `openpona` line below is checked by the parser (`python -m openpona parse "..."`) and by `tests/test_docs_examples.py`; a leading `!` marks a line expected INVALID, `?` one expected AMBIGUOUS. YAML and English live in `text`/`yaml` blocks, never in `openpona` blocks.

## The event in plain words

CI on pull request 678 went red. A colleague asked the agent to fix it.
The agent ran the fix, looked at the CI again, and saw it go green.

## Step 1 - see it as vectors

Start from directions, not from English words. We need: the CI tool (an instrument that does work), a state "not fit", a wish, a change, and the agent itself. The smallest tokens: `ilo pali` (instrument + work = the build/CI tool in this project's context), `pona` (fit), `kama` (become), `wile` (intend/desire), `jan linja` (the agent's own address).

Three candidate phrasings for "CI is red", all valid:

```openpona
ilo pali li pini ala             # candidate A: the build tool did not complete
ilo pali li pona ala             # candidate B: the build tool is not fit
ilo pali li kama ala             # candidate C: the build tool did not become (anything)
```

Chosen: B. A says the run is unfinished, which is also true while CI is still running, so it cannot tell "running" from "failed". C is too empty. B says the state of the tool is "not fit", which is what red means. What B cannot say is why (a failing test, a lint error): there is no token for it, and nothing may be invented. The reason belongs in the record (`literals`) or in a `tan` phrase that points at another address.

The green state is the mirror: `ilo pali li kama pona`, the tool became fit. The negative is `kama pi pona ala`: head `kama`, group `[pona ala]` — "became [not-good]"; the negation scopes over `pona`, not over `kama`, so "did not become fit" (`kama ala pona`) cannot be said under the `pi` shape (`canon/11`, Negation). Three units after `li` need `pi`; without it the line is INVALID.

```openpona
ilo pali li kama pona            # green: the tool became fit
ilo pali li kama pi pona ala     # became [not-good]: head kama, group [pona ala]
! ilo pali li kama pona ala      # three units after li, no pi
```

## Step 2 - state the context with `la`

A bare `ilo pali li pona ala` says nothing about which project. `la` situates validity, so put the scope in front: `ma pali` = the work/project scope.

```openpona
ma pali la ilo pali li pona ala  # in the project scope: the CI tool is not fit
```

Only one `la` fits in a statement. Do not stack a second context in front of it:

```openpona
! ma pali la lukin la ilo pali li pona ala   # two la clauses: not a statement
```

The project name, the repository and the PR number are not in the sentence. The sentence only has the tokens; the rest is the next step.

## Step 3 - bind addresses

The persisted form is the bound record (`canon/05_addressing.md`, `schema/statement.schema.json`). The surface is only its view. The number 678 appears exactly once, in the record.

```yaml
surface: ma pali la ilo pali li pona ala
context:
  tokens: [ma, pali]
  bound_ref: project:acme-web
subject:
  tokens: [ilo, pali]
  bound_ref: ci:run-4711          # the CI run itself; the PR number is a literal below
literals:
  pr_number: 678
  failing_job: unit-tests
actor: urn:agent:linja
resolution_context:
  - project:acme-web
  - repo:acme-web
resolution_status: RESOLVED
truth_status: observed
```

Resolution walks from the narrowest context outward and stops when exactly one candidate remains. If the project has two CI tools in scope (say a build service and a lint service, both matching `ilo pali`), the result is not a guess:

```yaml
surface: ma pali la ilo pali li pona ala
subject:
  tokens: [ilo, pali]
  candidates: [ci:build-service, ci:lint-service]
resolution_context: [project:acme-web]
resolution_status: AMBIGUOUS
```

Correct outcome: keep both candidates, do not bind, and either narrow the context (a more specific scope, or a two-token address that only one tool matches) or ask. "The newest PR" or "the tool used last" is not a reason to bind. This is a binding ambiguity; it is different from a parse ambiguity, where the sentence itself has two readings:

```openpona
? jan pali jan pali jan          # parse-ambiguous: D(jan pali) jan, or jan D(pali jan)
```

## Step 4 - truth status

Who said it, and how does the speaker stand to it? That is the `truth_status` field of the record, not part of the surface. Five of the seven statements of the full story (numbers 1, 2, 3, 5 and 7 in the closing block) carry the statuses:

| # | Surface | truth_status | actor | Note |
|---|---|---|---|---|
| 1 | `ma pali la ilo pali li pona ala` | observed | agent | read from the CI result, evidence: the check-run |
| 2 | `ma pali la jan ante li wile e kama pona` | requested | colleague | the ask; the actor is the colleague, not the agent |
| 3 | `ma pali la jan linja li pona e ilo pali` | intended | agent (`jan linja`) | a plan; not evidence that anything happened |
| 4 | `ma pali la nasin pona li pini` | observed | agent | the fix script exited 0 |
| 5 | `ma pali la ilo pali li kama pona` | observed | agent | the CI check itself turned green |

Record 4 is observed only about the script: exit code 0 says the command finished, not that the world reached the expected state (`canon/06`). Recording "CI is green" from it would be a claim without evidence. Record 5 is written only after the agent looked at the CI again, i.e. after `ma pali la jan linja li lukin e ilo pali`.

```yaml
surface: ma pali la jan linja li pona e ilo pali
subject: {tokens: [jan, linja], bound_ref: urn:agent:linja}   # the agent's own address = actor
object:  {tokens: [ilo, pali], bound_ref: ci:run-4711}
actor: urn:agent:linja
truth_status: intended
literals: {planned_commit_message: "fix flaky unit test"}
```

Research convention (H-TS, not canon): the status can also be carried as a prefix, with no new token. The record's field stays authoritative; the prefix is only an experiment (`research/truth_status_in_language.md`) — and a Toki Pona speaker reads `lukin la` as "apparently", which is one reason it is still research.

```openpona
lukin la ilo pali li pona ala               # H-TS prefix for observed
wile la jan ante li wile e kama pona        # H-TS prefix for requested
wile la jan linja li pona e ilo pali           # H-TS prefix for intended: same prefix as requested
```

The last two show why H-TS is open: `requested` and `intended` collapse into the same prefix, so the record would still need the field. A prefix also takes the single `la` slot, so it cannot be combined with `ma pali la` (see Step 2).

## Step 5 - what the runtime must refuse

OpenPona itself performs no effect. A runtime that reads these sentences must refuse:

```text
1. Executing the fix because the sentence looks like a command.
   `jan linja li pona e ilo pali` is an intention by the author. It maps to an action
   only through identity, authority, policy and preconditions checked by the
   runtime. Statement 2 (a `requested`) does not authorize anything by itself.

2. Recording the run as green before observing.
   "Script exited 0" is one observation. "CI is green" is another. Write the
   second record only after a fresh read of the CI status, with its evidence.

3. Binding to the most recent CI run when two match.
   Two candidates (the build service and the lint service above) means
   resolution_status AMBIGUOUS. Narrow the context or ask with `seme`; never
   bind to the most recent, the largest, or the only open one.
```

Each refusal keeps history honest: a bound record never changes after it is written, and a later context change does not rewrite what `ilo pali` meant on that day.

## The whole story in order

Seven statements, all RESOLVED. The comments are a reading, not a translation; the statuses are in the records above, not in the lines. The agent refers to itself by its own address, `jan linja`; `jan linja` would mean "this person" (decision 2026-10-01, `canon/11` departure 4).

```openpona
ma pali la ilo pali li pona ala          # 1 observed: CI on PR 678 is red (PR in the record)
ma pali la jan ante li wile e kama pona  # 2 requested by the colleague: wants it to become fit
ma pali la jan linja li pona e ilo pali     # 3 intended by the agent: will make the tool fit
ma pali la jan linja li pali e nasin pona   # 4 the agent works a fix (executed by the runtime)
ma pali la nasin pona li pini            # 5 observed: the fix route (nasin pona) ended = the script finished (exit 0, not yet green)
ma pali la jan linja li lukin e ilo pali    # 6 the agent inspects the CI again
ma pali la ilo pali li kama pona         # 7 observed: the CI became fit (green)
```

## Sentences wanted but not expressible

- "The unit test job failed" or any reason: no token for a specific check. Kept in `literals`.
- "The colleague asked the agent" as an addressed request: `jan ante li wile e ...` names the wish, but there is no addressee slot. The asker is the record's `actor`; the addressee is a further record field.
- "Which of two matching tools" cannot be said in the surface at all: a second token would change the address, and a name is not allowed. Only narrowing the context or asking with `seme` resolves it.
