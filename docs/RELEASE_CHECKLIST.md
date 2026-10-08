# Release checklist

Three version numbers are separate on purpose. Bumping one never implies bumping another.

| What | Current | Lives in | Changes when |
|---|---|---|---|
| Package version | `0.2.0` | `pyproject.toml` (`[project].version`), `MANIFEST.json` parser line | any released change to the Python package, tools or docs |
| Token inventory | `anu 1.1` | `MANIFEST.json` (`token_version`), `data/matrix.csv`, `canon/` | only by an author decision with a supersession ledger entry (the matrix is frozen; release housekeeping never edits it) |
| Parser API | `1.0.0` | `docs/parser-api.md`, `api_version` in parse results | the JSON shape of a parse result changes (semver: shape break = major) |

## Before tagging

- [ ] CI is green on the release commit: `tests` (3.11, 3.12), `conformance-counts`, `docs-lint`, `package-smoke`, `security`.
- [ ] `make check PYTHON=<venv python>` passes locally in an environment with `.[test]` installed (Hypothesis present; nothing skipped for a missing dependency).
- [ ] `make smoke-wheel PYTHON=<venv python>` passes (wheel built into a temp dir, fresh venv, conformance run from outside the checkout).
- [ ] Counts: `python tools/conformance_counts.py --check` exits 0. If the corpus changed, run `python tools/conformance_counts.py --write` and commit README.md and MANIFEST.json; never type counts by hand.
- [ ] `git diff <previous tag> -- canon data/matrix.csv SPEC.md` is empty, or every change has an author decision and a supersession ledger entry.
- [ ] The six baseline conformance files still match `conformance/BASELINE.lock`.
- [ ] `CHANGELOG.md` has an entry for the version, naming which of the three versions moved and why.
- [ ] Items marked `PENDING AUTHOR REVIEW` in the changelog are either decided by the author or still labelled as pending; none is presented as canon.
- [ ] Research-grade material (`research/`) is not referenced from canon or SPEC as established.
- [ ] Secret scan (`gitleaks`) and `pip-audit` pass in CI; no secrets in new fixtures.
- [ ] Tag `v<package version>` on the release commit; the token inventory and parser API versions are recorded in the release notes, not in the tag.

## Not automated here

- Publishing to a package index (no publish job exists; add one only after the author decides where releases go).
- A license scan beyond the committed `LICENSE*` files and `LICENSE_POLICY.md`.
