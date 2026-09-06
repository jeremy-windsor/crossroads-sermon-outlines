PYTHON := /usr/bin/python3
export PYTHONDONTWRITEBYTECODE := 1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
export PYTEST_ADDOPTS := -p no:cacheprovider --basetemp=.test-artifacts/pytest

.PHONY: render check test browser parity validate verify verify-live
render:
	$(PYTHON) site/render.py
check:
	$(PYTHON) site/render.py --check
test:
	mkdir -p .test-artifacts
	$(PYTHON) -m pytest tests/ -q
browser:
	mkdir -p .test-artifacts
	$(PYTHON) -m pytest tests/browser_checks.py -q
parity:
	$(PYTHON) tests/test_migration_parity.py --all
validate:
	$(PYTHON) tests/validate.py
verify: test parity check validate
	git diff --check
verify-live:
	$(PYTHON) tests/verify_live.py --all
