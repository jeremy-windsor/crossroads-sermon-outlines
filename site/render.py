#!/usr/bin/python3
"""Deterministic branch-root build. Reads content/site; writes only public output."""

import argparse
import json
from pathlib import Path
import re
import sys

from schema import SERIES_ID, SLUG, flatten, loads, loads_series, validate_series_collection
import templates

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = re.compile(rf"(?:index\.html|search\.html|search-index\.json|archive\.html|archive/\d{{4}}\.html|series\.html|series/{SERIES_ID}\.html|sermons/{SLUG}\.html|assets/site\.css)")
PUBLIC_PATTERNS = ("index.html", "search.html", "search-index.json", "archive.html", "archive/*.html", "series.html", "series/*.html", "sermons/*.html", "assets/site.css")


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


def series_records(root=ROOT, sermon_records=None):
    sermon_records = records(root) if sermon_records is None else sermon_records
    result = []
    for path in sorted((root / "content" / "series").glob("*.json")):
        series = loads_series(read_source(root, path.relative_to(root)))
        expected = f"content/series/{series['id']}.json"
        if path.relative_to(root).as_posix() != expected:
            raise ValueError(f"Series path mismatch: {path}")
        result.append(series)
    validate_series_collection(result, sermon_records)
    by_slug = {record["slug"]: record for record in sermon_records}
    return sorted(
        result,
        key=lambda series: (max(by_slug[member["slug"]]["published"] for member in series["members"]), series["id"]),
        reverse=True,
    )


def search_index(sermon_records, series_records):
    """Index only meaningful reader-visible sermon content with stable anchors."""
    membership = templates.series_membership(series_records)
    documents = []
    for record in sermon_records:
        series, _, _ = membership[record["slug"]]
        common = [record["title"], record["speaker"], record["published"], templates.date_label(record["published"]), series["name"]]
        sermon_url = f"sermons/{record['slug']}.html"
        context = f"{record['speaker']} · {templates.date_label(record['published'])} · {series['name']}"
        documents.append({
            "kind": "sermon",
            "title": record["title"],
            "context": context,
            "excerpt": f"{series['name']} · {record['speaker']} · {templates.date_label(record['published'])}",
            "url": sermon_url,
            "terms": "\n".join(common),
        })
        nodes = {node["id"]: node for node in flatten(record["movements"])}
        for node in nodes.values():
            documents.append({
                "kind": "overview",
                "title": f"{node['heading']} — {record['title']}",
                "context": context,
                "excerpt": node["bullets"][0],
                "excerpts": node["bullets"],
                "url": sermon_url + "#" + node["id"],
                "terms": "\n".join(common + [node["heading"], *node["bullets"]]),
            })
        for row in record["ledger"]:
            node = nodes[row["anchor_node_id"]]
            documents.append({
                "kind": "scripture",
                "title": f"{row['reference']} — {record['title']}",
                "context": f"Scripture ledger · {node['heading']} · {context}",
                "excerpt": row["phrase"],
                "reference": row["reference"],
                "url": sermon_url + "#ledger-" + row["id"],
                "terms": "\n".join(common + [row["reference"], row["phrase"], row["treatment"], node["heading"]]),
            })
    return {"version": 1, "documents": documents}


def build(root=ROOT):
    """Pure output plan: no public files read, created, or modified."""
    data = records(root)
    series_data = series_records(root, data)
    scripts = tuple(read_source(root, "site/assets/" + name) for name in ("theme-init.js", "theme.js"))
    search_script = read_source(root, "site/assets/search.js")
    index_bytes = (json.dumps(search_index(data, series_data), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output = {
        "index.html": templates.home(data, series_data, scripts),
        "search.html": templates.search(scripts, search_script),
        "search-index.json": index_bytes,
        "archive.html": templates.archive(data, scripts),
        "series.html": templates.series_index(data, series_data, scripts),
        "assets/site.css": read_source(root, "site/assets/site.css"),
    }
    for year in sorted({record['published'][:4] for record in data}):
        output[f"archive/{year}.html"] = templates.year_archive(year, [r for r in data if r['published'][:4] == year], series_data, scripts)
    by_slug = {record["slug"]: record for record in data}
    for series in series_data:
        output[f"series/{series['id']}.html"] = templates.series_page(series, by_slug, series_data, scripts)
    for i, record in enumerate(data):
        previous = data[i + 1] if i + 1 < len(data) else None
        following = data[i - 1] if i else None
        output[f"sermons/{record['slug']}.html"] = templates.sermon(record, previous, following, scripts, series_data)
    return {path: value.encode('utf-8') if isinstance(value, str) else value for path, value in sorted(output.items())}


def public_path(root, relative):
    path = root / relative
    if not PUBLIC.fullmatch(relative) or path.resolve() != root.resolve() / relative:
        raise ValueError(f"Not an allowed public output: {relative}")
    return path


def existing_public(root):
    return {path.relative_to(root).as_posix() for pattern in PUBLIC_PATTERNS for path in root.glob(pattern)}


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
