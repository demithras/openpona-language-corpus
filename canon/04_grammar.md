# 04 — Grammar

**Status: CANON with explicit parser-design boundary.**

## 1. Principle: vectors before parts of speech

Do not begin by assigning a token an English noun/verb label. Each semantic token (and `tan`) is first a direction of semantic/operational change; the five particles have structural force only. Syntactic role emerges from composition and structural position.

## 2. Semantic units

A semantic unit may be:

- one primitive token;
- a two-token composed concept/address;
- a `pi`-grouped larger concept;
- a META-derived repetition of a one- or two-token unit of semantic tokens or `tan`.

## 3. Structural positions

Since 2026-10-28 (rule N2, §3.1) the `phrase` of the grammar below has two forms: any phrase of one or more tokens in predicate position, and a phrase of at least two tokens in every nominal position. The EBNF is the grammar before N2 with the length condition stated as a comment; §3.1 is the normative text.

A structural token is interpreted structurally when it connects valid semantic units in a grammatical position:

```ebnf
statement  = clause , [ "la" , clause ]
           | "tan" , expression , "la" , clause ;              (* source context; one statement per line *)
clause     = expression , { "li" , predicate } ;      (* a predicate containing anu must be the last one *)
predicate  = expression , { "e" , expression } , { "tan" , expression }
           | "tan" , expression , { "tan" , expression } ;          (* source predicate takes no objects *)
expression = phrase , [ "anu" , expression ] ;
phrase     = head , { "pi" , unit , unit } ;
head       = unit , [ unit ] ;                      (* N2: one token only in predicate position *)
unit       = semantic-token | "tan" | meta-unit ;
```

Precedence, loosest to tightest: `la` → `li` → `e`/`tan` → `anu` → `pi` (Toki Pona's order for `la li e pi`; the place of `anu` is OpenPona's own choice).

One statement per line. Spaces (U+0020) and tabs (U+0009) before and after the statement are ignored, and so is exactly one trailing line boundary (LF, or CR LF). Anything else around or inside the statement — a leading newline, a second trailing newline, a lone CR, U+2028, U+2029, U+0085, VT, FF, FS, NBSP — makes the line INVALID (author decision 2026-10-09; SPEC invariant 17).

`li la e pi anu` outside these positions make the statement INVALID. In OpenPona `tan` is the only token with both a structural and a vector role (Toki Pona has more prepositions — `canon/11`, departure 1, declared). Directly after `li` it is a source predicate (`jan pali li tan ma pali`) and at the start of a statement before `la` a source context (`tan toki ni la jan pali li pali`), decisions 2026-10-01; objects come before source phrases; the structural reading wins wherever one exists, and the vector reading applies only where none does (`jan pali li tan ma e ijo pona`).

`anu` joins phrases only, never whole clauses (author decision, 2026-09-30), and a predicate containing `anu` must be the last predicate of its clause (`jan pali li pali anu jan pali li awen` is INVALID — decision 2026-10-01). A choice between statements is written as two `la` statements on two lines (`nasin open la jan pali li pali` / `nasin awen la jan pali li awen`).

### 3.1 Phrase length by position (rule N2)

Author decision 2026-10-28, replacing the earlier rule that `head = unit , [ unit ]` is valid in every position (a one-unit phrase could be a subject, object, source or context). The reason: the role of a phrase becomes recoverable from its length. *A verb is not always one token, but if a phrase is one token, it is definitely a verb.*

**N2.** A phrase of exactly one token is allowed only in predicate position. Every phrase in a nominal position has at least two tokens. A reading that breaks N2 is dropped.

Counting: surface tokens covered by the phrase (semantic tokens, and `tan` read as a vector unit). Particles and a structural `tan` are never counted. A META unit counts its surface tokens: `ilo ilo` = `D1(ilo)` = 2 tokens, `ilo ilo ilo` = 3. A phrase with a `pi` group has three or more tokens and always passes. In an `anu` expression every alternative is a phrase and is checked on its own against the position of the whole expression.

| Position | Where | Length |
|---|---|---|
| P1 predicate | the main expression directly after `li` (before any `e` or structural `tan`), every `anu` alternative included | >= 1 |
| P2 predicate | a bare statement: one clause with no `li` and no `la` (read as a predicate) | >= 1 |
| N-a subject | the expression before the first `li` of a clause | >= 2 |
| N-b object | every expression after `e` | >= 2 |
| N-c source | every expression after a structural `tan` (source phrase, source predicate `X li tan Y`, the `Y` of `tan Y la S`) | >= 2 |
| N-d context | a clause before `la` without `li`; the clause after `la` without `li` | >= 2 |

A context clause with its own `li` follows the rows above for its subject, predicate and objects.

```openpona
ilo pali li awen
ilo pali li pona ala
pali
ilo pali
ma pali la ilo pali li awen
! ilo li awen
! jan pali li pali e ilo
! ma la ilo pali li awen
```

`ilo li awen` is INVALID (subject `ilo` has one token); `ilo pali li awen` is valid because the predicate `awen` may have one token. `pali` and `ilo pali` are valid statements: a bare statement is read as a predicate.

Order (author decision 2026-10-28, round 2): the priority of §5 (META, then structure, then vector) runs exactly as before N2, over the readings that are valid without N2; then every selected reading that breaks N2 is dropped. **N2 is checked on the readings the priority rules select; it never revives a reading they removed.** Zero readings left is INVALID, one is RESOLVED, several are AMBIGUOUS, so N2 can turn an AMBIGUOUS selection into RESOLVED or INVALID but never changes which fold or which `tan` reading is selected. Wherever `tan` can be structural it is structural: `jan pali li tan ma` is INVALID (source `ma` has one token), it does not fall back to the vector phrase `{tan ma}`, and `jan pali li kama tan ma` is INVALID (its vector reading `kama tan ma` has three units without `pi` anyway). A META fold never changes the token count of a phrase (`D_n(P)` counts `n + 1` copies of `P`), so the META step and N2 do not interact. The diagnostic of an INVALID line names the position and the token.

Toki Pona accepts `ilo li pona`; OpenPona does not. N2 is a declared strictness (`canon/11`, departure 12).

## 4. Grouping

A two-unit concept can be juxtaposed directly:

```text
ilo sitelen
sona pali
```

A single concept containing three or more semantic units requires explicit `pi` grouping. This rule exists to prevent invisible phrase-boundary decisions.

The head is one or two units; every `pi` group is exactly two units; several groups each modify the head (Toki Pona reading, no nesting).

```text
ilo pi sona lawa               valid
jan ilo pi sona lawa           valid
jan pi ilo sona pi sona lawa   valid (two groups on head jan)
sona pi lawa                   INVALID  (two units never take pi)
ilo sona pi lawa               INVALID  (group of one)
jan ilo sona                   INVALID  (three units, no pi)
```

## 5. META priority

Repetition is recognized before normal structural interpretation, and structure is recognized before the vector reading of `tan`:

```text
META → structure → vector
```

The three levels combine lexicographically (author decision 2026-10-09; SPEC invariant 18 and §7). Among all valid readings keep those whose the set of token positions covered by META folds is maximal by inclusion; among them keep those whose set of structural `tan` positions is maximal by inclusion; one survivor is RESOLVED, several incomparable survivors are AMBIGUOUS. A META fold is applied only where the resulting reading is valid: if folding a repeated run makes the statement invalid, the unfolded reading is used (the same principle as for `tan`, the lower-priority reading applies where the higher one does not parse).

```openpona
jan pi ilo ilo
jan pi ma ma
? jan pali li ilo tan tan ma pi ijo ante
ma pali li tan ma pali tan ma ma
```

`jan pi ilo ilo` and `jan pi ma ma` are RESOLVED unfolded (`{jan pi ilo ilo}`); `jan pali li ilo tan tan ma pi ijo ante` is AMBIGUOUS (one structural `tan` at each of two positions; both source phrases have two or more tokens, rule N2); `ma pali li tan ma pali tan ma ma` is RESOLVED as `({ma pali} li tan {ma pali} tan {D1(ma)})`.

If `P` is a valid unit of one or two tokens — semantic tokens or `tan` only, never a particle — `n` consecutive copies of `P` form one META unit `D^(n-1)(P)`:

```text
P P        D(P)
P P P      D^2(P)
tan tan    D(tan)      (META beats the structural reading)
```

Particles never fold: `li li li`, `e e`, `la la jan li pali` are INVALID, and `jan pali li pali li pali` is two predicates, not `D(li pali)` (clarified 2026-10-01 after review).

The derivative operator composes:

```text
D^m(D^n(P)) = D^(m+n)(P)
```

Only the resulting depth is meaningful (`D^2(D^2(P)) = D^4(P)`); there is no separate surface form for a nested derivative.

## 6. Ambiguity is a value

A parser/runtime must support at least:

```text
RESOLVED
AMBIGUOUS
UNRESOLVED
INVALID
```

It must not turn `AMBIGUOUS` into a guessed binding merely because one interpretation is more convenient.

A parser produces the first, second and fourth; `UNRESOLVED` is a binding outcome (an address with no candidate) and belongs to the runtime, not to the parse.

## 7. Parser-design boundary

The reference parser in `openpona/` implements the grammar above and is checked by `conformance/`. Deep-repetition boundaries remain an area where the conformance corpus, not prose, is the authority: a new case changes the parser, not the other way round. Any implementation must preserve the invariants above and expose unresolved ambiguity.
