# Learn OpenPona

This tutorial teaches the current language without requiring the reader to know the project history.

The target is not conversational fluency in a miniature natural language. The target is **operational fluency**: seeing a situation as vectors, composing a compact address, stating context and relation, preserving uncertainty, and keeping intention separate from reality.

## Lesson 0 — The mental model

Start with one rule:

> A token is a direction of meaning before it is a word class.

`open` is not merely the English verb *open*. It points toward initiation, exposure of possibility and making something addressable.

`awen` is not merely *stay*. It points toward persistence, retention and holding.

`ante` points toward difference/transformation.

The small vocabulary works by composing these directions.

## Lesson 1 — Learn the matrix as six narratives and seven operations

Memorize by rows first:

```text
1 open    lon     tawa    wile    pali    pilin   li
2 seme    ma      lukin   sona    ni      kute    la
3 nasin   sijelo  ilo     lawa    awen    ken     e
4 jan     ante    kama    sama    ijo     selo    tan
5 sitelen linja   pana    toki    tenpo   pini    pi
6 sike    ale     weka    ala     kulupu  pona    anu
```

Row narratives:

```text
1 Start → Ground
2 Question → Locate
3 Commit → Practice
4 Encounter → Transform
5 Understand → Structure
6 Generalize → Release
```

Column roles (the planet is only a mnemonic alias):

```text
Seed       (Sun)
Map        (Moon)
Explore    (Mars)
Decide     (Mercury)
Work       (Jupiter)
Resonate   (Venus)
Structure  (Saturn)
```

Do not add the row/column labels to the 42-token vocabulary. They are coordinates/mnemonics.

### Exercise

Without looking up the table, answer:

- row 2, column 2;
- row 5, column 3;
- row 6, column 7.

Answers: `ma`, `pana`, `anu`.

## Lesson 2 — Separate semantic and structural tokens

The Structure column contains the six structural operators:

```text
li la e tan pi anu
```

Basic forces:

```text
X li P      X has/is-in predicate/state/process P
P e Y       P is directed toward Y
C la S      S holds in context/condition C
S tan Z     S derives from / depends on / is caused by Z
H pi U U    a group of exactly two units modifies the head H
A anu B     explicit alternative/branch/version
```

As in Toki Pona, `li la e pi anu` are particles only: outside their position the statement is invalid. `tan` is the one OpenPona token that is both a particle ("from") and an ordinary word (source/cause). Toki Pona has more prepositions (`lon`, `tawa`, `sama`, `kepeken`), which OpenPona reads as ordinary words; see `canon/11`, departure 1.

## Lesson 3 — Build concepts and addresses

Two semantic units can create a context-relative concept:

```text
ilo sitelen
```

Think *instrument-for-representation*, not a fixed dictionary translation.

```text
sona pali
```

Think *operational/work knowledge*.

Order matters:

```text
ilo sitelen ≠ sitelen ilo
```

For a single concept with three or more semantic units, show grouping explicitly with `pi`: the head is one or two words, each `pi` adds a group of exactly two.

```text
ilo pi sona lawa
sona pali pi ken pali
jan pi ilo sona pi sona lawa
```

`sona pi lawa` (two words) and `ilo sona pi lawa` (group of one) are invalid.

The grammar tells the runtime what belongs together even when the exact natural-language rendering varies.

## Lesson 4 — Bind addresses to reality

OpenPona addresses are not globally unique IDs.

A runtime resolves from narrow context outward:

```text
local context → parents → domain/project → wider graph → unresolved
```

If exactly one object matches, bind its stable machine reference.

If zero match: `UNRESOLVED`.

If several match: `AMBIGUOUS`.

Never guess and then write the guess into history as fact.

### Exercise

Two objects in one project both match `ilo sitelen`. What is the correct result?

**Answer:** `AMBIGUOUS`, unless context is narrowed or an explicit alternative is retained.

## Lesson 5 — Write operational statements

Examples:

```text
ilo sitelen li awen
jan pali li pana e sitelen
ma pali la jan li lukin e ijo
sona ni li kama tan kute
nasin open anu nasin awen
```

Write one statement per line. Do not focus on one perfect English translation. Ask instead:

1. what expressions are present?
2. what structural relation connects them?
3. what context binds the addresses?
4. what is the truth/speech-act status?

## Lesson 6 — Preserve epistemic status

The same semantic expression can be:

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

This distinction normally lives in the bound statement/runtime metadata.

An intended `pali` is not an observed result. A returned HTTP 200 is not an observed world outcome.

## Lesson 7 — Use `seme` and `anu` instead of guessing

`seme` keeps a variable/question unresolved.

`anu` keeps branches explicit.

This is one of the most important operational habits in OpenPona: ambiguity is represented as state, not erased by confident prose.

## Lesson 8 — META through repetition

If `P` is a valid semantic unit:

```text
P P
```

means a semantic derivative/meta operation over `P`.

Repeated META composes:

```text
D^m(D^n(P)) = D^(m+n)(P)
```

The parser recognizes repetition before ordinary structural splitting.

Do not assume one universal English gloss for every META depth.

## Lesson 9 — Know what the language does not do

OpenPona syntax does not grant authority.

It does not decide expert judgment simply because authority is known.

It does not make a command result into an observed outcome.

It does not remove the need for stable IDs, typed data, evidence or transaction semantics in an executable system.

## Lesson 10 — The EOO challenge

A current research challenge asks whether the language can encode a typed ontology surface for:

```text
ObjectType Property LinkType Interface
Function Action Policy Authority
Observation Version Constraint
```

Do not assume the answer is yes.

The strong test is lossless compilation to an independent typed IR. If OpenPona needs hidden sidecars or new primitives for core meaning, it fails that strong role while potentially remaining useful for humans/agents.

## Suggested practice

For a real event from your work:

1. identify the signal/observation;
2. choose the smallest OpenPona vectors that describe it;
3. state the current context;
4. bind every entity address or mark ambiguity;
5. record whether it is observed, requested, intended or hypothesized;
6. if action is proposed, separately state what evidence would count as observed success.

This practice keeps the language connected to reality rather than turning it into a private poetic code.
