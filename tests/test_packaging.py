"""Packaging: the token table ships inside the package."""
from pathlib import Path

import openpona
from openpona import TOKENS

ROOT = Path(__file__).resolve().parent.parent


def test_packaged_tokens_match_canonical_copy():
    assert (ROOT / "openpona" / "tokens.csv").read_bytes() == (ROOT / "data" / "tokens.csv").read_bytes()


def test_loader_stays_inside_the_package():
    assert len(TOKENS) == 42
    src = Path(openpona.__file__).read_text(encoding="utf-8")
    assert "parent.parent" not in src


def test_ci_workflow_fails_when_hypothesis_is_missing():
    """TP-12: ci.yml has a hard `import hypothesis` step (not continue-on-error)."""
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "import hypothesis" in text
    assert "continue-on-error" not in text
    for job in ("tests:", "conformance-counts:", "docs-lint:", "package-smoke:", "security:"):
        assert f"\n  {job}" in text, job


def test_versions_are_separate_and_consistent():
    import json
    import re
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    py = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'^version = "0\.2\.0"$', py, re.M)
    assert manifest["token_version"] == "anu 1.1"
    assert "0.2.0" in manifest["parser"]
    checklist = (ROOT / "docs" / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    for v in ("`0.2.0`", "`anu 1.1`", "`1.0.0`"):
        assert v in checklist
