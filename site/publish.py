#!/usr/bin/python3
"""Publish already-committed main. Never edit, stage, commit, or render files."""

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import render
from validation import validate_surfaces
from verify_live import LIVE, verify


def git(*arguments):
    return subprocess.check_output(['git', *arguments], cwd=ROOT, text=True).strip()


def preflight(run=git):
    if run('branch', '--show-current') != 'main':
        raise RuntimeError('Publication requires reviewed changes already committed on main')
    if run('status', '--porcelain', '--untracked-files=normal'):
        raise RuntimeError('Publication requires a clean working tree')
    expected = render.build()
    errors = render.check(ROOT, expected)
    if errors:
        raise RuntimeError('\n'.join(errors))
    if not set(expected) <= set(run('ls-files').splitlines()):
        raise RuntimeError('Generated output is not fully tracked')
    validate_surfaces(expected, render.records())
    return expected


def publish(run=git, live=verify):
    expected = preflight(run)
    # Git receives a normal fast-forward push; a concurrent remote update fails safely.
    run('push', 'origin', 'HEAD:main')
    run('fetch', 'origin', 'main')
    if run('rev-parse', 'HEAD') != run('rev-parse', 'origin/main'):
        raise RuntimeError('Local HEAD and origin/main differ after push')
    live(LIVE, expected, render.records())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true', help='Read-only publication preflight')
    group.add_argument('--push', action='store_true', help='Push already-reviewed main and verify live bytes')
    args = parser.parse_args()
    if args.check:
        preflight()
        print('Publication preflight passed; nothing pushed')
    else:
        publish()


if __name__ == '__main__':
    main()
