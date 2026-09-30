.PHONY: test check conformance docs

test:
	python -m pytest -q

check: test
	@echo "OpenPona corpus integrity checks passed."

conformance:
	python -m openpona conformance

docs:
	python -m pytest -q tests/test_docs_examples.py
