# Migrating legacy records to the record profiles

Classification: **ENGINEERING**. Companion of `docs/record-profiles.md` (TP-03). Nothing here
changes canon, the token inventory (`anu 1.1`) or the legacy schema, which stays as it is.

A *legacy record* is anything written against `schema/statement.schema.json` or the
template in `docs/for-agents.md` section 6 before the profiles existed. It is never
rewritten in place. Migration produces a **new** record next to it.

## Policy

1. **Append-only.** The legacy record is kept unchanged. The migrated record is a new
   artifact; it may reuse the legacy `statement_id` only if the legacy store is retired
   in the same step, otherwise give it a new id and set `supersedes` to the old one.
2. **Never invent.** Migration copies what the legacy record says and refuses where it
   would have to make something up (below). Unknown is recorded as unknown.
3. **Keep the remainder.** Every legacy field with no home in the profiles is preserved
   under `x-legacy` (not sealed, not part of the binding). Open questions are listed under
   `x-migration`.
4. **Seal at migration time.** The migrated binding is sealed with the revision the
   migration was done against (`source_revision`). The seal says "this is the binding as
   migrated", not "this is the binding as it was resolved originally"; the provenance
   kind `legacy_migration` says so.
5. **History does not move.** If a legacy `bound_ref` would resolve differently today, the
   migrated record still carries the legacy `bound_ref`. A different resolution is a
   separate new record with `supersedes`.

## Field mapping

| Legacy field | New location | Note |
|---|---|---|
| `statement_id` | `statement_id` | copied; must match the id pattern |
| `surface` | `surface`, and `tokens` | re-parsed; an `INVALID` surface cannot be migrated |
| `tokens` (top level) | `tokens` | taken from the parse; the legacy copy is kept in `x-legacy.tokens` |
| `parse_status` | `parse_reference.status` for `RESOLVED` / `AMBIGUOUS` | `UNRESOLVED` and `INVALID` there are not parse results; the legacy value is kept in `x-legacy.parse_status` and the binding status is recomputed |
| (none) | `parse_reference` | pinned against the current parser (`api_version`, `alternative_index`, `ast_sha256`) |
| (none) | `schema_version`, `token_version`, `profile` | `records-1.0.0`, `anu 1.1`, `AgentEvent` or `BoundStatement` |
| `subject` / `object` / `context` `{tokens, bound_ref, candidates, meta_depth}` | same names, with `resolution_status` | `RESOLVED` if `bound_ref`; `AMBIGUOUS` if 2+ candidates and none bound; else `UNRESOLVED`. `meta_depth` is derivable from the AST and moves to `x-legacy.<role>` |
| `predicate` | `predicate` (`{tokens}`) | |
| `resolution_context` or `context_refs` | `resolution_context` | if absent: empty, with `x-migration.resolution_context = "unknown in the legacy record"` |
| `resolution_status` (template) | recomputed | aggregate of the entities |
| `candidates` (template, top level) | per entity | kept in `x-legacy.candidates` if it cannot be attributed to an entity |
| `truth_status`, `actor`, `created_at`, `literals`, `cause_refs` | same names | copied |
| `evidence` or `evidence_refs` | `evidence_refs` | |
| `source_event` | `provenance.source_event` | with `provenance.kind` `legacy_migration` |
| `branch`, `context_refs`, anything else | `x-legacy` | preserved verbatim |

## Which profile a migrated record gets

* **AgentEvent**, when the legacy record has `statement_id`, `created_at` (a real RFC 3339
  value), `actor`, `truth_status` and a non-empty resolution context.
* **BoundStatement** otherwise, with `x-migration.missing_for_agent_event` naming what is
  missing. Nothing is guessed to upgrade it.

## Refusals

`openpona.binding.migrate_legacy` raises `MigrationError` instead of producing a record when:

| Situation | Why |
|---|---|
| the surface does not parse (`INVALID`, `RESOURCE_EXHAUSTED`) | a record cannot pin a parse that does not exist |
| the surface has an ambiguous parse and no `alternative_index` is given | the legacy record cannot say which reading was meant |
| `truth_status` is `observed` and there is no evidence | an unevidenced observation is not carried over (CHANGE_GATES 5); supply the evidence, or re-status the record as a new statement |
| a legacy `token_version` other than `anu 1.1` | a different inventory is a different language version |
| the migrated record fails validation | the helper validates its own output |

A record that cannot be migrated stays as legacy; do not edit it to make it pass.

## Procedure

```text
1. Freeze the legacy store (read-only). Note its revision: that is source_revision.
2. For each record:  new = openpona.binding.migrate_legacy(old, source_revision=REV)
                     (pass alternative_index=N for an ambiguous surface)
3. python -m openpona validate-record new.json           must exit 0
4. Write `new` next to `old`; keep `old`.
5. Review the x-migration notes. Resolve them by writing NEW records, never by editing.
```

`openpona.binding.migrate_legacy` is a convenience. It has no knowledge of any particular
store (Logseq or otherwise), and only the legacy shapes named above were tried against it
(the walkthrough's bound-record examples and synthetic ones in `tests/test_records.py`).

## Later changes after migration

| Change wanted | Do |
|---|---|
| a `bound_ref` was wrong | write a new record with `supersedes`; the migrated one stays |
| the context was unknown and is now known | write a new record with `supersedes` and the context; do not fill `resolution_context` in place |
| add a note | an `x-` key may be added; it is outside the seal |
| the parser API changes shape | records with the old major fail with `parse_api_incompatible`; re-pin by migrating again (new record) |

## Open points (**PENDING AUTHOR REVIEW**)

* Whether the legacy schema should be marked deprecated, and from which release.
* Whether `legacy_migration` provenance should lower the standing of a migrated
  `observed` claim (the policy above only refuses unevidenced ones).
* The id policy when a store is retired in place (rule 1).
