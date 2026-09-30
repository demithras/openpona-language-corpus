.PHONY: test check conformance

test:
	python -m pytest -q

check: test
	@echo "OpenPona corpus integrity checks passed."

conformance:
	python -m openpona conformance
