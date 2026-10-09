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

A structural token is interpreted structurally when it connects valid semantic units in a grammatical position:

```ebnf
statement  = clause , [ "la" , clause ]
           | "tan" , expression , "la" , clause ;              (* source context; one statement per line *)
clause     = expression , { "li" , predicate } ;      (* a predicate containing anu must be the last one *)
predicate  = expression , { "e" , expression } , { "tan" , expression }
           | "tan" , expression , { "tan" , expression } ;          (* source predicate takes no objects *)
expression = phrase , [ "anu" , expression ] ;
phrase     = head , { "pi" , unit , unit } ;
head       = unit , [ unit ] ;
unit       = semantic-token | "tan" | meta-unit ;
```

Precedence, loosest to tightest: `la` → `li` → `e`/`tan` → `anu` → `pi` (Toki Pona's order for `la li e pi`; the place of `anu` is OpenPona's own choice).

One statement per line. Spaces (U+0020) and tabs (U+0009) before and after the statement are ignored, and so is exactly one trailing line boundary (LF, or CR LF). Anything else around or inside the statement — a leading newline, a second trailing newline, a lone CR, U+2028, U+2029, U+0085, VT, FF, FS, NBSP — makes the line INVALID (author decision 2026-10-09; SPEC invariant 17).

`li la e pi anu` outside these positions make the statement INVALID. In OpenPona `tan` is the only token with both a structural and a vector role (Toki Pona has more prepositions — `canon/11`, departure 1, declared). Directly after `li` it is a source predicate (`jan li tan ma`) and at the start of a statement before `la` a source context (`tan ni la jan li pali`), decisions 2026-10-01; objects come before source phrases; the structural reading wins wherever one exists, and the vector reading applies only where none does (`jan li tan ma e ijo`).

`anu` joins phrases only, never whole clauses (author decision, 2026-09-30), and a predicate containing `anu` must be the last predicate of its clause (`jan li pali anu jan li awen` is INVALID — decision 2026-10-01). A choice between statements is written as two `la` statements on two lines (`nasin open la jan li pali` / `nasin awen la jan li awen`).

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
? jan li ilo tan tan ma
ma li tan ma tan ma ma
```

`jan pi ilo ilo` and `jan pi ma ma` are RESOLVED unfolded (`{jan pi ilo ilo}`); `jan li ilo tan tan ma` is AMBIGUOUS (one structural `tan` at each of two positions); `ma li tan ma tan ma ma` is RESOLVED as `({ma} li tan {ma} tan {D1(ma)})`.

If `P` is a valid unit of one or two tokens — semantic tokens or `tan` only, never a particle — `n` consecutive copies of `P` form one META unit `D^(n-1)(P)`:

```text
P P        D(P)
P P P      D^2(P)
tan tan    D(tan)      (META beats the structural reading)
```

Particles never fold: `li li li`, `e e`, `la la jan li pali` are INVALID, and `jan li pali li pali` is two predicates, not `D(li pali)` (clarified 2026-10-01 after review).

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
