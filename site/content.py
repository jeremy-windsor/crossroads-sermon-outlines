#!/usr/bin/python3
"""Content-phase writer: validated JSON on stdin; one canonical record written."""

import argparse
from pathlib import Path
import sys

from schema import dumps, loads

ROOT = Path(__file__).resolve().parents[1]


def write_record(root, record):
    data = dumps(record)  # Validate before creating anything.
    target = root / "content" / "sermons" / record["published"][:4] / (record["slug"] + ".json")
    if target.resolve() != root.resolve() / target.relative_to(root):
        raise ValueError("Content destination escapes content/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate stdin without writing")
    args = parser.parse_args()
    record = loads(sys.stdin.read())
    if args.check:
        print(f"Valid record: {record['slug']}")
    else:
        print(write_record(ROOT, record).relative_to(ROOT))


if __name__ == "__main__":
    main()
