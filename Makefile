.PHONY: test check

test:
	python -m pytest -q

check: test
	@echo "OpenPona corpus integrity checks passed."
