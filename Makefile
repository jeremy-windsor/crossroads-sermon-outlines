PYTHON := /usr/bin/python3
export PYTHONDONTWRITEBYTECODE := 1

.PHONY: render check

# Build the site from content/.
render:
	$(PYTHON) site/render.py

# Records validate and committed pages match content/.
check:
	$(PYTHON) site/render.py --check
	$(PYTHON) -m pytest tests/ -q -p no:cacheprovider
