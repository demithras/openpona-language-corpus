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
predicate   = expression , "li" , expression ;
directed    = expression , "e"  , expression ;
contextual  = expression , "la" , expression ;
causal      = expression , "tan", expression ;
alternative = expression , "anu", expression ;
```

`pi` is a grouping operator rather than a simple binary relation.

If the token occurs outside a valid structural position, a strict parser must not blindly force the structural interpretation. It may remain a semantic vector or produce `AMBIGUOUS`.

## 4. Grouping

A two-unit concept can be juxtaposed directly:

```text
ilo sitelen
sona pali
```

A single concept containing three or more semantic units requires explicit `pi` grouping. This rule exists to prevent invisible phrase-boundary decisions.

Example:

```text
sona pali pi ken pali
```

## 5. META priority

Repetition is recognized before normal structural interpretation. If `P` is a valid completed unit:

```text
P P
```

represents a meta/essence/semantic derivative of `P`.

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
