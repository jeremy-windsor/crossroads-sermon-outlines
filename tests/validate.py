#!/usr/bin/python3
"""Validate every generated local surface without changing any file."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'site'))
import render
from validation import validate_surfaces


if __name__ == '__main__':
    expected = render.build()
    errors = render.check(render.ROOT, expected)
    if errors:
        raise SystemExit('\n'.join(errors))
    actual = {path: (render.ROOT / path).read_bytes() for path in expected}
    print(validate_surfaces(actual, render.records()))
