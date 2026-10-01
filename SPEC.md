# OpenPona Language Specification

**Specification family:** OpenPona  
**Canonical token inventory:** `anu 1.1`  
**Consolidation date:** 2026-10-01  
**Status:** CANON where explicitly marked; unresolved points are called out.

## 1. Definition

OpenPona is a **42-token Executable Operational Language (EOL)** for describing agency, context, relation, transition, observation, intention and state in a compact compositional form.

*Executable* means that a resolved OpenPona statement can be bound and executed by an external runtime (§10). The language itself performs no effects and grants no authority.

Its kernel is:

```text
OpenPona = 36 semantic tokens (vectors) + 6 structural tokens (particles; tan is also a vector)
```

The language is intentionally small. New domains should normally be expressed by **composition and contextual binding**, not by adding new primitive tokens.

OpenPona is not merely a reduced dialect of Toki Pona. It reuses lexical forms but assigns them stable operational roles inside its own matrix, grammar and addressing system.

**OpenPona is designed not to contradict Toki Pona.** The design rule: every valid OpenPona statement is a valid Toki Pona sentence, and its OpenPona parse coincides with a Toki Pona parse at the level of particle structure. OpenPona may be *stricter* than Toki Pona (fewer words, mandatory `pi`, no `mi`/`sina`/`o`) and may *add meaning* inside a phrase (META, head/group semantics); it must never accept what Toki Pona rejects. **Status of the claim:** a design principle, verified so far only for rejection cases (`conformance/toki_pona_compat.jsonl`); an independent review on 2026-10-01 found departures that are listed, with their status, in `canon/11_toki_pona_compatibility.md`.

## 2. Core invariants

The following are canonical:

1. **Exactly 42 canonical tokens** in the `anu 1.1` inventory.
2. **36 semantic + 6 structural** architecture.
3. The six structural tokens are exactly `li la e tan pi anu`.
4. Every semantic token (and `tan`) is first interpretable as a **vector/operator/direction**, not as a fixed English noun; the five particles `li la e pi anu` have structural force only.
5. Two or more semantic tokens can form a **context-resolved concept or entity address**.
6. Token order matters; `A B` is not assumed equivalent to `B A`.
7. Context narrows meaning; `la` is the primary explicit context operator.
8. Ambiguity is represented, not guessed. Use unresolved state, `seme`, or `anu` branching.
9. Persisted statements bind machine identity at write time so later context changes do not rewrite history.
10. Intent/request is distinct from observation/fact.
11. `li la e pi anu` are structural only, as in Toki Pona. `tan` is both structural (source phrase) and semantic (vector), as in Toki Pona; where a structural reading of `tan` exists it wins, and the vector reading applies only where no structural parse exists.
12. **META parsing has priority** over ordinary structural parsing.
13. Repetition of a token or well-formed phrase denotes a meta/essence/derivative operation over that semantic unit.
14. Three or more semantic units forming one noun/concept must use explicit grouping with `pi` (§5.3).
15. Natural-language renderings are secondary views; they must not silently alter operational semantics.
16. **Toki Pona compatibility** (§1): OpenPona may be stricter than Toki Pona and may add meaning, but never accepts what Toki Pona rejects. Known departures are tracked in `canon/11`.
17. One statement per line. The language has no punctuation.
18. Parse priority: META (repetition) → structure (particles) → vector reading of `tan`.

## 3. Canonical matrix

| Row / narrative arc | Seed (Sun) | Map (Moon) | Explore (Mars) | Decide (Mercury) | Work (Jupiter) | Resonate (Venus) | Structure (Saturn) |
|---|---|---|---|---|---|---|---|
| 1 Start → Ground | `open` | `lon` | `tawa` | `wile` | `pali` | `pilin` | `li` |
| 2 Question → Locate | `seme` | `ma` | `lukin` | `sona` | `ni` | `kute` | `la` |
| 3 Commit → Practice | `nasin` | `sijelo` | `ilo` | `lawa` | `awen` | `ken` | `e` |
| 4 Encounter → Transform | `jan` | `ante` | `kama` | `sama` | `ijo` | `selo` | `tan` |
| 5 Understand → Structure | `sitelen` | `linja` | `pana` | `toki` | `tenpo` | `pini` | `pi` |
| 6 Generalize → Release | `sike` | `ale` | `weka` | `ala` | `kulupu` | `pona` | `anu` |

The row/column labels are **external metadata**, not extra OpenPona primitives. The functional label (Seed, Map, …) is the operational name of the column; the planet is a mnemonic alias only. Internal, unpublished experiments (`research/matrix_coordinate_experiments.md`, MX2–MX3) suggested the first row/column act as embedded projections of broader axes; the coordinate generator is research, not grammar.

## 4. Token operational glosses

The glosses are directional anchors, not exhaustive dictionaries.

```text
open     initiate / expose possibility / make addressable
lon      assert presence / reality / situated existence
tawa     direct / move / orient
wile     target / intend / desire
pali     execute / work / make
pilin    evaluate / sense / affective registration

seme     query / unresolved variable
ma       locate / scope / situate
lukin    inspect / observe intentionally
sona     know / resolve / model
ni       bind / point / fix current referent
kute     receive / listen / accept signal

nasin    route / method / procedure
sijelo   embody / instantiate physically
ilo      instrument / tool / means
lawa     control / govern / regulate
awen     retain / persist / hold
ken      enable / permit / possibility

jan      agentify / actor / responsible agency
ante     transform / difference
kama     become / transition / arrive
sama     match / align / equivalence
ijo      reify / make thing-like / entity
selo     bound / surface / interface / enclosure

sitelen  represent / encode / inscribe
linja    link / thread / chain
pana     emit / give / publish / send
toki     communicate / articulate / exchange meaning
tenpo    temporalize / process through time
pini     close / terminate / complete

sike     iterate / cycle / recurse
ale      totalize / universal scope
weka     remove / distance / detach
ala      negate / absence / deny
kulupu   group / aggregate / collective
pona     normalize / improve / make fit

li       predication / state relation
la       context / condition / validity scope
e        directed object / target
tan      source / cause / dependency / provenance
pi       grouping / composition scope
anu      alternative / branch / version
```

## 5. Semantic expressions

### 5.1 Primitive expression

A single token may operate as a vector:

```text
open
lukin
pini
```

This does not make the token a globally unique noun.

### 5.2 Composed concept/address

Two semantic units may form a concept or address:

```text
ilo sitelen
sona pali
linja toki
```

The leading unit acts as the head unless context or an explicit grammar rule says otherwise.

### 5.3 Grouped concept

When a single concept contains three or more semantic units, grouping must be explicit with `pi` so the parser does not silently invent phrase boundaries.

The shape is fixed:

- the **head** is one or two units;
- each `pi` introduces a group of **exactly two** units (Toki Pona requires two or more after `pi`; OpenPona never leaves a group of one, so exactly two);
- several `pi` groups are allowed; each modifies the head, as in Toki Pona, they do not nest.

```text
ilo pi sona lawa              head ilo,        group [sona lawa]
jan ilo pi sona lawa          head jan ilo,    group [sona lawa]
sona pali pi ken pali         head sona pali,  group [ken pali]
jan pi ilo sona pi sona lawa  head jan,        groups [ilo sona] [sona lawa]

sona pi lawa                  INVALID: two units never take pi
ilo sona pi lawa              INVALID: group of one
jan ilo sona                  INVALID: three units without pi
```

Multiple `pi` groups are accepted by the grammar; Toki Pona usage treats them as a grey zone, so prefer one group where the meaning allows.

The exact interpretation is context-dependent, but the grouping is not.

## 6. Structural grammar

Structural operators are strongest when they connect complete semantic expressions:

```text
X li P                 predicate; several predicates: X li P li Q
P e Y                  object; several objects: P e Y e Z
P tan Z                source; e and tan phrases in any order: P tan Z e Y
C la S                 context
X pi Y Z               grouping (§5.3)
A anu B                alternative between phrases
```

Precedence, loosest to tightest, as in Toki Pona: `la` → `li` → `e`/`tan` → `anu` → `pi`. `anu` joins phrases only (`jan li pali anu awen`); it never joins whole clauses. A choice between whole statements is written as two context statements on two lines:

```text
nasin open la jan li pali
nasin awen la jan li awen
```

`jan li pali anu jan li awen` therefore has exactly one parse — `jan` does (`pali` or `jan`) and `awen` — and is not a branch between statements (author decision, 2026-09-30).

Interpretive anchors:

- `li`: predicate/state relation;
- `la`: context/condition/validity scope;
- `e`: directed target/object;
- `tan`: source/cause/dependency/provenance;
- `pi`: grouping/composition scope;
- `anu`: explicit alternative/branch/version.

A structural token outside a valid structural position makes the statement INVALID, as in Toki Pona (`li pali`, `la jan li pali`, `jan pi li pali` are all invalid). The one exception is `tan`, which is also a semantic vector (`seme li tan e ni`, `jan tan li pali`).

## 7. META and repetition

META has parsing priority.

If `P` is a valid unit of one or two tokens — semantic tokens or `tan`; the particles `li la e pi anu` never form META units — repetition applies a semantic derivative/meta operation:

```text
P P
```

Conceptually:

```text
D(P)
```

Repeated derivation composes:

```text
D^m(D^n(P)) = D^(m+n)(P)
```

`n` repetitions of `P` denote `D^(n-1)(P)`. Only the resulting depth is meaningful: `D^2(D^2(P)) = D^4(P)` exactly as snap is the acceleration of acceleration, and there is no separate surface form for a nested derivative.

In Toki Pona usage a repeated word reads as emphasis; OpenPona assigns it derivative meaning. This adds meaning on top of a valid Toki Pona phrase and does not change its syntax, so it is compatible under §1.

This rule is canonical at the algebraic level; the exact natural-language gloss of derivative depth is context-dependent and must not be hard-coded as one English word.

## 8. Addressing and binding

An OpenPona address is the **shortest ordered semantic composition that uniquely resolves an entity in current context**.

Resolution order:

```text
explicit local context
→ parent/ancestor context
→ project/domain context
→ wider graph context
→ unresolved
```

Rules:

- machine identity is a stable UUID/reference;
- OpenPona address is contextual and may change;
- historical statements retain the machine binding used at write time;
- if more than one entity remains valid, do not guess;
- `seme` marks unresolved/query state; `anu` can express explicit alternatives.

### 8.1 Speaker

OpenPona has no `mi`/`sina`. **`jan ni` denotes the author of the statement** (the speaking agent or person). It is an ordinary contextual address whose binding is the statement's `actor`; it does not introduce a first person into the grammar.

```text
jan ni li lukin e ilo sitelen      the author of this statement inspects the logging tool
```

### 8.2 External values

The surface text contains **only the 42 tokens** — never numbers, identifiers, quoted strings or proper names. An external value (a PR number, a UUID, a file name, a timestamp) lives in the bound statement (`bound_ref`, `literals`) and the surface points at it by address:

```text
ilo pali li pini ala                surface
subject.bound_ref: pr:678           record
```

This is not a hidden sidecar: the bound statement is the canonical persisted form (§8, `schema/statement.schema.json`), and the surface is its human/agent view.

## 9. Truth and speech-act status

OpenPona surface text alone is insufficient to distinguish fact from desire. A runtime must preserve a truth/speech-act status such as:

```text
observed
asserted
requested
intended
hypothesis
inferred
unknown
rejected
```

OpenPona must never be used to overwrite contradictory raw evidence merely because a preferred narrative is simpler.

Whether this status can be carried inside the surface with existing tokens (`lukin la X` = observed, `wile la X` = intended, `seme la X` = unknown) is a research hypothesis, not canon: see `research/truth_status_in_language.md`.

## 10. Runtime boundary

OpenPona may represent operational meaning, but execution requires a runtime that resolves identity, authority, policy and effects.

The language itself does not grant permission. In particular:

- a statement that resembles an action request is not authority;
- a successful command is not proof of an observed outcome;
- domain judgment need not be computable from authority structure;
- grounding adapters may normalize observations but must not silently contain business judgment if the experiment claims semantic/runtime separation.

## 11. Encodings

The canonical transport representation is Latin token text. Alternative visual or spoken encodings may map to the same 42 token IDs, but they must be treated as codecs rather than new semantics.

No glyph/font assets are included in this repository.

## 12. Versioning

`anu 1.0` already had the 36+6 architecture but used an older Sprint 5 ordering. `anu 1.1` corrected Sprint 5 to:

```text
sitelen linja pana toki tenpo pini pi
```

Later accepted grammar rules in this repository consolidate the language without changing the 42-token inventory; therefore this corpus does not invent an `anu 1.2` token version.

## 13. Explicit exclusions

The following are not canonical primitives:

```text
mute
kalama
nimi
```

Older materials that use different token inventories or structural sets are historical evidence only.

## 14. Research boundary

The following are active hypotheses, not language facts:

- the exact 6 × 7 matrix is the unique optimal arrangement;
- all 42 tokens can be generated uniquely from external row/column coordinates;
- OpenPona is a complete Ontology Language for Palantir-class EOO;
- OpenPona is technically necessary for EOO;
- OpenPona improves human cognition beyond mnemonic/internalized use.

See `research/` for evidence and falsifiers.
