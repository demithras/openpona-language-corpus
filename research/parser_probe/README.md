# Parser probe — 2026-09-30

**Status: RESEARCH — superseded by `canon/04_grammar.md` on 2026-09-30.** This records the probe that preceded the author's decisions; the assumed rules below were accepted (precedence, one statement per line) or replaced (the `pi` shape, clause-level `anu`). The current parser is described by canon, not by this file.

## Question

Can the OpenPona structural grammar be written as a small context-free grammar that:

1. parses the corpus examples with exactly one interpretation each;
2. rejects 3+ unit concepts without `pi` (SPEC invariant 14);
3. decides by position alone whether `li la e tan pi anu` act structurally or as vectors (SPEC invariant 11), without introducing ambiguity?

## Method

The grammar engine of [nim-ka/tpparser](https://github.com/nim-ka/tpparser) (a Toki Pona parser that returns *all* interpretations of a sentence) was run in Node against two draft grammars:

| File | Rule 11 (structural tokens also vectors) |
|---|---|
| `op_strict.txt` | no — the six structural tokens are only structural |
| `op_dual.txt` | yes — the six tokens are also admitted as semantic units |

tpparser has no license, so its code is not included here; only the two grammar files written for this probe are.

### Assumed rules (the part that needs an author decision)

```text
sentence   = clause [la clause]                 # la is outermost
clause     = expression [li predicate]          # li splits subject / predicate
predicate  = expression [e expression] [tan expression]
expression = phrase [anu expression]            # anu joins expressions, right-nested
phrase     = unit | unit unit
           | unit pi unit unit | unit unit pi unit | unit unit pi unit unit
```

Precedence, loosest to tightest: `la` → `li` → `e`/`tan` → `anu` → `pi`. This matches Toki Pona convention for `la li e pi`.

## Results (18 sentences)

| Sentence | strict | dual |
|---|---|---|
| `ilo sitelen li awen` | 1 | 1 |
| `jan pali li pana e sitelen` | 1 | 1 |
| `ma pali la jan li lukin e ijo` | 1 | 1 |
| `sona ni li kama tan kute` | 1 | 1 |
| `nasin open anu nasin awen` | 1 | 1 |
| `seme li tan e ni` | INVALID | 1 (`tan` = predicate vector) |
| `ma pali la ilo sitelen` | 1 | 1 |
| `sona pali pi ken pali` | 1 | 1 |
| `sona pali ken` | INVALID | INVALID |
| `ilo sitelen ilo sitelen` | INVALID | INVALID |
| `jan li pali e ijo tan ma la ilo li pini` | 1 | 1 |
| `jan tan li pali` | INVALID | 1 |
| `sona li kama tan tan` | INVALID | 1 |
| `jan li pali e ijo tan` | INVALID | 1 |
| `ilo tan pi jan pali li awen` | INVALID | 1 |
| `sona pali pi ken pali anu ala` | 1 | 1 |
| `jan li tan e ma tan kute` | INVALID | 1 |
| `ilo li awen ala` | 1 | 1 |

## Findings

1. **Rule 11 is decidable by position under these assumptions.** The dual grammar accepted every positional-vector use of `tan` and produced exactly one parse per sentence — no added ambiguity on this set. *(fact for these 18; hypothesis that it generalizes)*
2. **The `pi` rule is enforceable by grammar.** `sona pali ken` is rejected, `sona pali pi ken pali` is accepted. *(fact)*
3. **META cannot be a context-free rule.** `P P → D(P)` needs "the same unit twice", which a CFG cannot express. It must be a pre-pass before the structural parse — exactly what SPEC invariant 12 (META has priority) implies. *(model)*
4. **Negation fell out as a modifier.** `ilo li awen ala` parsed as predicate phrase `awen ala`. This is a grammar accident, not a canon rule for negation scope (review gap L4). *(fact + caveat)*
5. The corpus sentence `seme li tan e ni` needs rule 11 to parse at all; under a strict grammar the corpus's own example is invalid. *(fact)*

## Falsifiers for the assumed rules

- A natural sentence the author considers valid that the dual grammar rejects or parses twice.
- A case where `anu` must bind looser than `li` (e.g. branching whole clauses: `jan li pali anu jan li awen`) — decided 2026-09-30: `anu` joins phrases only; see `canon/11` departure 2 for the caveat.

## Consequence

The reference parser (`openpona/`) now implements `canon/04`, which superseded this draft on 2026-09-30.
