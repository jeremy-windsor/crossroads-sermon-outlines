#!/usr/bin/python3
"""Deterministic branch-root build. Reads content/site; writes only public output."""

import argparse
from pathlib import Path
import re
import sys

from schema import SLUG, loads
import templates

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = re.compile(rf"(?:index\.html|archive\.html|archive/\d{{4}}\.html|sermons/{SLUG}\.html|assets/site\.css)")


def read_source(root, relative):
    path = root / relative
    if not any(path.resolve().is_relative_to(root.resolve() / directory) for directory in ("content", "site")):
        raise ValueError("Renderer reads only content/ and site/")
    return path.read_text(encoding="utf-8")


def records(root=ROOT):
    result = []
    for path in sorted((root / "content" / "sermons").glob("*/*.json")):
        record = loads(read_source(root, path.relative_to(root)))
        expected = f"content/sermons/{record['published'][:4]}/{record['slug']}.json"
        if path.relative_to(root).as_posix() != expected:
            raise ValueError(f"Record path mismatch: {path}")
        result.append(record)
    if not result:
        raise ValueError("No sermon records found")
    return sorted(result, key=lambda r: (r['published'], r['slug']), reverse=True)


def build(root=ROOT):
    """Pure output plan: no public files read, created, or modified."""
    data = records(root)
    scripts = tuple(read_source(root, "site/assets/" + name) for name in ("theme-init.js", "theme.js"))
    output = {
        "index.html": templates.home(data, scripts),
        "archive.html": templates.archive(data, scripts),
        "assets/site.css": read_source(root, "site/assets/site.css"),
    }
    for year in sorted({record['published'][:4] for record in data}):
        output[f"archive/{year}.html"] = templates.year_archive(year, [r for r in data if r['published'][:4] == year], scripts)
    for i, record in enumerate(data):
        previous = data[i + 1] if i + 1 < len(data) else None
        following = data[i - 1] if i else None
        output[f"sermons/{record['slug']}.html"] = templates.sermon(record, previous, following, scripts)
    return {path: value.encode('utf-8') for path, value in sorted(output.items())}


def public_path(root, relative):
    path = root / relative
    if not PUBLIC.fullmatch(relative) or path.resolve() != root.resolve() / relative:
        raise ValueError(f"Not an allowed public output: {relative}")
    return path


def existing_public(root):
    return {path.relative_to(root).as_posix() for pattern in ("index.html", "archive.html", "archive/*.html", "sermons/*.html", "assets/site.css") for path in root.glob(pattern)}


def check(root, output):
    errors = []
    for relative, expected in output.items():
        path = public_path(root, relative)
        if not path.is_file() or path.read_bytes() != expected:
            errors.append(f"Stale or missing: {relative}")
    errors.extend(f"Unexpected generated page: {p}" for p in sorted(existing_public(root) - output.keys()))
    return errors


def write(root, output):
    # Validate every destination before touching any output. Never silently delete pages.
    paths = {relative: public_path(root, relative) for relative in output}
    extras = existing_public(root) - output.keys()
    if extras:
        raise ValueError(f"Unexpected public pages require review: {sorted(extras)}")
    for relative, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(output[relative])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare all expected bytes without writing")
    args = parser.parse_args()
    output = build()
    if args.check:
        errors = check(ROOT, output)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print(f"Render check: {len(output)}/{len(output)} generated files match")
    else:
        write(ROOT, output)
        print(f"Rendered {len(output)} files from {len(records())} sermon records")
    return 0


if __name__ == "__main__":
    sys.exit(main())
