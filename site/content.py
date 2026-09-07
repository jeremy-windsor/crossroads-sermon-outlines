#!/usr/bin/python3
"""Content-phase writer for validated sermon and series JSON on stdin."""

import argparse
from pathlib import Path
import sys

from schema import dumps, dumps_series, loads, loads_series, validate_series_collection

ROOT = Path(__file__).resolve().parents[1]


def write_record(root, record):
    data = dumps(record)  # Validate before creating anything.
    target = root / "content" / "sermons" / record["published"][:4] / (record["slug"] + ".json")
    if target.resolve() != root.resolve() / target.relative_to(root):
        raise ValueError("Content destination escapes content/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8")
    return target


def collection_with_candidate(root, candidate):
    records = []
    for path in sorted((root / "content" / "sermons").glob("*/*.json")):
        record = loads(path.read_text(encoding="utf-8"))
        expected = root / "content" / "sermons" / record["published"][:4] / f"{record['slug']}.json"
        if path.resolve() != expected.resolve():
            raise ValueError(f"Sermon path mismatch: {path}")
        records.append(record)
    series_records = []
    for path in sorted((root / "content" / "series").glob("*.json")):
        series = loads_series(path.read_text(encoding="utf-8"))
        expected = root / "content" / "series" / f"{series['id']}.json"
        if path.resolve() != expected.resolve():
            raise ValueError(f"Series path mismatch: {path}")
        if series["id"] != candidate["id"]:
            series_records.append(series)
    series_records.append(candidate)
    return validate_series_collection(series_records, records)


def write_series(root, series):
    data = dumps_series(series)
    target = root / "content" / "series" / f"{series['id']}.json"
    if target.resolve() != root.resolve() / target.relative_to(root):
        raise ValueError("Content destination escapes content/")
    collection_with_candidate(root, series)  # Validate the full replacement before writing.
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series", action="store_true", help="Read a series record instead of a sermon record")
    parser.add_argument("--check", action="store_true", help="Validate stdin without writing")
    args = parser.parse_args()
    if args.series:
        series = loads_series(sys.stdin.read())
        collection_with_candidate(ROOT, series)
        if args.check:
            print(f"Valid series: {series['id']}")
        else:
            print(write_series(ROOT, series).relative_to(ROOT))
    else:
        record = loads(sys.stdin.read())
        if args.check:
            print(f"Valid record: {record['slug']}")
        else:
            print(write_record(ROOT, record).relative_to(ROOT))


if __name__ == "__main__":
    main()
