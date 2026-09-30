# OpenPona Language Specification

**Specification family:** OpenPona  
**Canonical token inventory:** `anu 1.1`  
**Consolidation date:** 2026-09-29  
**Status:** CANON where explicitly marked; unresolved points are called out.

## 1. Definition

OpenPona is a **42-token operational language** for describing agency, context, relation, transition, observation, intention and state in a compact compositional form.

Its kernel is:

```text
OpenPona = 36 semantic vectors + 6 structural vectors
```

The language is intentionally small. New domains should normally be expressed by **composition and contextual binding**, not by adding new primitive tokens.

OpenPona is not merely a reduced dialect of Toki Pona. It reuses lexical forms but assigns them stable operational roles inside its own matrix, grammar and addressing system.

## 2. Core invariants

The following are canonical:

1. **Exactly 42 canonical tokens** in the `anu 1.1` inventory.
2. **36 semantic + 6 structural** architecture.
3. The six structural tokens are exactly `li la e tan pi anu`.
4. Every token is first interpretable as a **vector/operator/direction**, not as a fixed English noun.
5. Two or more semantic tokens can form a **context-resolved concept or entity address**.
6. Token order matters; `A B` is not assumed equivalent to `B A`.
7. Context narrows meaning; `la` is the primary explicit context operator.
8. Ambiguity is represented, not guessed. Use unresolved state, `seme`, or `anu` branching.
9. Persisted statements bind machine identity at write time so later context changes do not rewrite history.
10. Intent/request is distinct from observation/fact.
11. Structural tokens take structural force only in structural position between semantic expressions; outside that position they remain semantic vectors.
12. **META parsing has priority** over ordinary structural parsing.
13. Repetition of a token or well-formed phrase denotes a meta/essence/derivative operation over that semantic unit.
14. Three or more semantic units forming one noun/concept must use explicit grouping with `pi`.
15. Natural-language renderings are secondary views; they must not silently alter operational semantics.

## 3. Canonical matrix

| Row / narrative arc | Sun / Seed | Moon / Map | Mars / Explore | Mercury / Decide | Jupiter / Work | Venus / Resonate | Saturn / Structure |
|---|---|---|---|---|---|---|---|
| 1 Start → Ground | `open` | `lon` | `tawa` | `wile` | `pali` | `pilin` | `li` |
| 2 Question → Locate | `seme` | `ma` | `lukin` | `sona` | `ni` | `kute` | `la` |
| 3 Commit → Practice | `nasin` | `sijelo` | `ilo` | `lawa` | `awen` | `ken` | `e` |
| 4 Encounter → Transform | `jan` | `ante` | `kama` | `sama` | `ijo` | `selo` | `tan` |
| 5 Understand → Structure | `sitelen` | `linja` | `pana` | `toki` | `tenpo` | `pini` | `pi` |
| 6 Generalize → Release | `sike` | `ale` | `weka` | `ala` | `kulupu` | `pona` | `anu` |

The row/column labels are **external metadata**, not extra OpenPona primitives. Recent experiments support treating the first row/column as embedded projections of broader axes, but the exact coordinate generator is research, not grammar.

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

```text
sona pali pi ken pali
```

The exact interpretation is context-dependent, but the grouping is not.

## 6. Structural grammar

Structural operators are strongest when they connect complete semantic expressions:

```text
X li P
P e Y
C la S
S tan Z
X pi Y
A anu B
```

Interpretive anchors:

- `li`: predicate/state relation;
- `la`: context/condition/validity scope;
- `e`: directed target/object;
- `tan`: source/cause/dependency/provenance;
- `pi`: grouping/composition scope;
- `anu`: explicit alternative/branch/version.

If a structural token is not in a valid structural position between semantic expressions, it is not silently discarded; it may be interpreted as its own vector meaning or rejected as ambiguous by a strict parser.

## 7. META and repetition

META has parsing priority.

If `P` is a valid semantic unit or completed phrase, repetition applies a semantic derivative/meta operation:

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

Equivalent repeated forms may normalize structurally (for example four repetitions can be grouped as two repeated pairs) without changing the derived semantic depth.

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
