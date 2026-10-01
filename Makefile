PYTHON ?= python

.PHONY: test conformance docs check

test:
	$(PYTHON) -m pytest -q

conformance:
	$(PYTHON) -m openpona conformance

docs:
	$(PYTHON) -m pytest -q tests/test_docs_examples.py

check: test conformance docs
	@echo "OpenPona corpus integrity checks passed."
