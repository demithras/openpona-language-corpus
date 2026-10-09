PYTHON ?= python
SMOKE_TMP ?=

.PHONY: test conformance docs counts lift check smoke-wheel

test:
	$(PYTHON) -m pytest -q

conformance:
	$(PYTHON) -m openpona conformance

docs:
	$(PYTHON) -m pytest -q tests/test_docs_examples.py

counts:
	$(PYTHON) tools/conformance_counts.py --check

lift:
	$(PYTHON) research/lift/blind_experiment.py validate
	$(PYTHON) -m unittest discover -s research/lift/tests

check: test conformance docs counts lift
	@echo "OpenPona corpus integrity checks passed."

# Build the wheel into a temp dir, install it into a FRESH venv (no editable install, no
# repo on sys.path) and run the conformance corpus shipped inside the wheel from outside
# the repository against the corpus in this checkout (conformance/ is not shipped in the
# wheel; the sdist carries it, see MANIFEST.in).  Needs network (or a pip cache) for lark unless PIP_FIND_LINKS is set.
smoke-wheel:
	@set -e; \
	root="$$(pwd)"; \
	tmp="$$(mktemp -d)"; trap 'rm -rf "$$tmp"' EXIT; \
	$(PYTHON) -m build --wheel --outdir "$$tmp/dist" "$$root" >"$$tmp/build.log" 2>&1 || { cat "$$tmp/build.log"; exit 1; }; \
	$(PYTHON) -m venv "$$tmp/venv"; \
	"$$tmp/venv/bin/python" -m pip install --quiet --disable-pip-version-check -c "$$root/constraints.txt" "$$tmp"/dist/*.whl; \
	cd "$$tmp"; \
	"$$tmp/venv/bin/python" -c "import openpona,sys; p=openpona.__file__; assert '$$root' not in p, p; print('installed from', p)"; \
	"$$tmp/venv/bin/python" -m openpona conformance --dir "$$root/conformance" | tee "$$tmp/conf.log" | tail -1; \
	grep -Eq '^[1-9][0-9]* passed, 0 failed' "$$tmp/conf.log"; \
	"$$tmp/venv/bin/python" -m openpona parse "jan li pali" ; \
	echo "smoke-wheel passed."
