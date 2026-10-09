# OpenPona cheat sheet

42 tokens (36 semantic + 6 structural), one grammar, no other words. Parser is the source of truth: `python -m openpona parse "ilo sitelen li awen"` prints RESOLVED / AMBIGUOUS / INVALID and the skeletons. In `openpona` code blocks a leading `!` marks a line that is expected INVALID and `?` one that is expected AMBIGUOUS; `D1(x)` is the META reading of `x x` (one derivative: `lukin lukin` = the looking-at-looking, inspection as such).

## The matrix (6 rows x 7 columns)

| Row | Lift (R) | Narrative | Seed · Identity | Map · Ground | Explore · Transform | Decide · Select | Work · Realize | Resonate · Evaluate | Structure |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Process | Start > Ground | `open` | `lon` | `tawa` | `wile` | `pali` | `pilin` | `li` |
| 2 | Inquiry | Question > Locate | `seme` | `ma` | `lukin` | `sona` | `ni` | `kute` | `la` |
| 3 | Method | Commit > Practice | `nasin` | `sijelo` | `ilo` | `lawa` | `awen` | `ken` | `e` |
| 4 | Agency | Encounter > Transform | `jan` | `ante` | `kama` | `sama` | `ijo` | `selo` | `tan` |
| 5 | Representation | Understand > Structure | `sitelen` | `linja` | `pana` | `toki` | `tenpo` | `pini` | `pi` |
| 6 | Integration | Generalize > Release | `sike` | `ale` | `weka` | `ala` | `kulupu` | `pona` | `anu` |

Column names are functional and carry the canonical Lift axis names (rows R1-R6, columns C1-C7; canon since 2026-10-09, `canon/03_matrix.md`); they are labels, never tokens. That the labels generate the tokens is research. A planetary mnemonic for the columns is in LEARN, Lesson 1. The last column is exactly the 6 structural tokens.

## The 42 glosses (vector first, not part of speech)

| | | | | | |
|---|---|---|---|---|---|
| `open` initiate, expose | `lon` presence, reality | `tawa` move, orient | `wile` intend, target | `pali` execute, make | `pilin` sense, evaluate |
| `seme` query, unknown | `ma` locate, scope | `lukin` inspect, observe | `sona` know, model | `ni` bind, point | `kute` receive signal |
| `nasin` route, method | `sijelo` embody | `ilo` tool, means | `lawa` govern | `awen` retain, persist | `ken` possibility |
| `jan` agent, actor | `ante` difference | `kama` become, arrive | `sama` match | `ijo` entity | `selo` boundary |
| `sitelen` represent | `linja` link, chain | `pana` emit, give | `toki` communicate | `tenpo` time | `pini` close, complete |
| `sike` iterate, cycle | `ale` all, universal | `weka` remove | `ala` negate, absent | `kulupu` group | `pona` improve, fit |

## Structural tokens and precedence

```text
X li P      predicate         P e Y      directed target     P e Y tan Z   objects, then source phrases
C la S      context, then S   H pi U U   group of exactly two units      A anu B       alternative phrases (a predicate with anu is the last one)
X li tan Z  source predicate (X derives from Z)      tan Z la S    source context (because of Z: S)
X anu seme  question idiom: X, or unknown?
```

Precedence, loosest to tightest: `la` > `li` > `e`/`tan` > `anu` > `pi`. `li la e pi anu` are particles only; `tan` is also a vector where no structural reading exists (`kama tan tan` = `kama D1(tan)`).

## The 8 rules that matter

1. Vector first: read each token as a direction of change, then let position decide its role.
2. Phrase = head (1-2 units) + any number of `pi` groups of exactly 2 units. Three units need `pi`; `sona pi lawa` is INVALID.
3. META: n repetitions of a 1- or 2-token unit = D^(n-1). META beats structure, structure beats the vector reading.
4. `tan` is the only dual token in OpenPona (source phrase, source predicate after `li`, or vector); the other five never carry content.
5. One statement per line. `anu` joins phrases only; a choice between statements is two `la` lines.
6. No `mi` or `sina`: an agent names itself by its own address (`jan linja`); `jan ni` means "this person", as in Toki Pona.
7. Values never in the surface: no numbers, ids, names, punctuation. They live in the record (`bound_ref`, `literals`).
8. Ambiguity is a value: RESOLVED, AMBIGUOUS, INVALID (parse) and UNRESOLVED (binding). Never guess a binding.

## Truth status (a field of the record, not of the surface)

`observed` `asserted` `requested` `intended` `hypothesis` `inferred` `unknown` `rejected`

Research only (H-TS, not canon): carrying status as a `lukin la` / `sona la` / `wile la` / `seme la` prefix in the surface.

## Canonical sentences

```openpona
ilo sitelen li awen              # the logging tool persists
jan pali li pana e sitelen       # a work agent emits a representation
ma pali la jan li lukin e ijo    # in project scope, an agent inspects an entity
sona ni li kama tan kute         # the bound knowledge came from a received signal
nasin open anu nasin awen        # opening path or retaining path
jan linja li lukin e ilo sitelen # the agent LINJA inspects the logging tool (self-reference by address)
! sona pi lawa                   # pi needs exactly two units after it; a two-unit concept takes no pi
! jan ilo sona                   # three units without pi
! li pali                        # particle with no subject
! la jan li pali                 # la needs a context clause before it
```

## Toki Pona

OpenPona is designed not to contradict Toki Pona: stricter yes, new meaning yes, accepting what Toki Pona rejects never. Verification is partial; known departures are listed in `canon/11`.
