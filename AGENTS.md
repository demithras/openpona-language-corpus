# Agent rules for this repository

An agent editing OpenPona must preserve the distinction between **canon**, **research**, and **history**.

## Required behavior

Before proposing a canon change:

1. identify the exact current rule it would replace;
2. state a falsifiable reason for the change;
3. create or update a research hypothesis first;
4. preserve the old rule in `history/supersession_ledger.md`;
5. update executable integrity tests;
6. never add a 43rd primitive merely to make one domain easier.

## Anti-contamination rule

Do not use the claim "OpenPona is the EOO Ontology Language" as an assumption inside this repository. That is tested in the companion EOO hypothesis pack (not yet published).

## Ambiguity rule

If a surface phrase has more than one plausible parse or binding, preserve the ambiguity. A strict parser should return an unresolved result rather than invent context.
