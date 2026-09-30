# 04 — Grammar

**Status: CANON with explicit parser-design boundary.**

## 1. Principle: vectors before parts of speech

Do not begin by assigning a token an English noun/verb label. Each token is first a direction of semantic/operational change. Syntactic role emerges from composition and structural position.

## 2. Semantic units

A semantic unit may be:

- one primitive token;
- a two-token composed concept/address;
- a `pi`-grouped larger concept;
- a completed clause;
- a META-derived repetition of a valid unit.

## 3. Structural positions

A structural token is interpreted structurally when it connects valid semantic units in a grammatical position:

```ebnf
statement  = clause , [ "la" , clause ] ;                 (* one statement per line *)
clause     = expression , { "li" , predicate } ;
predicate  = expression , { "e" , expression | "tan" , expression } ;
expression = phrase , [ "anu" , expression ] ;
phrase     = head , { "pi" , unit , unit } ;
head       = unit , [ unit ] ;
unit       = semantic-token | "tan" | meta-unit ;
```

Precedence, loosest to tightest, as in Toki Pona: `la` → `li` → `e`/`tan` → `anu` → `pi`.

`li la e pi anu` outside these positions make the statement INVALID. `tan` is the only token with both a structural and a vector role, as in Toki Pona; the structural reading wins wherever it exists.

Whether `anu` may join whole clauses is open (research); the grammar above joins phrases only.

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

If `P` is a valid unit of one or two tokens, `n` consecutive copies of `P` form one META unit `D^(n-1)(P)`:

```text
P P        D(P)
P P P      D^2(P)
tan tan    D(tan)      (META beats the structural reading)
```

The derivative operator composes:

```text
D^m(D^n(P)) = D^(m+n)(P)
```

Repeated groups may normalize without semantic loss. The parser must preserve derivative depth even if the surface form is normalized.

## 6. Ambiguity is a value

A parser/runtime must support at least:

```text
RESOLVED
AMBIGUOUS
UNRESOLVED
INVALID
```

It must not turn `AMBIGUOUS` into a guessed binding merely because one interpretation is more convenient.

## 7. Parser-design boundary

The corpus does not yet claim a single final concrete parsing algorithm for every nested expression. In particular, completed-phrase boundary recognition under deep repetition and mixed structural/semantic uses remains an implementation question. Any implementation must preserve the invariants above and expose unresolved ambiguity.
