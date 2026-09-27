PYTHON := /usr/bin/python3
export PYTHONDONTWRITEBYTECODE := 1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD := 1
export PYTEST_ADDOPTS := -p no:cacheprovider --basetemp=.test-artifacts/pytest

.PHONY: render check test browser verify-live

# Build the site from content/.
render:
	$(PYTHON) site/render.py

# The publish gate: pages match content, pages validate, unit tests pass.
check:
	mkdir -p .test-artifacts
	$(PYTHON) site/render.py --check
	$(PYTHON) tests/validate.py
	$(PYTHON) -m pytest tests/ -q --ignore=tests/browser_checks.py
	git diff --check

test: check

# Optional: real Chromium layout checks. Needs Playwright and local sockets.
browser:
	mkdir -p .test-artifacts
	$(PYTHON) -m pytest tests/browser_checks.py -q

# Optional: confirm GitHub Pages serves the committed bytes.
verify-live:
	$(PYTHON) tests/verify_live.py --all
