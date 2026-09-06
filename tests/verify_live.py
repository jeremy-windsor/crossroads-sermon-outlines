#!/usr/bin/python3
"""Read-only HTTP + byte equality + parsed validation for every generated surface."""

import argparse
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'site'))
import render
from validation import validate_surfaces

LIVE = 'https://jeremy-windsor.github.io/crossroads-sermon-outlines/'


def fetch(url):
    request = Request(url, headers={'Cache-Control': 'no-cache', 'User-Agent': 'Crossroads-site-verifier/2'})
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f'HTTP {response.status}: {url}')
        return response.read()


def verify(base_url, expected, records, attempts=6, delay=10, getter=fetch, sleeper=time.sleep):
    """Bounded propagation retries; never replaces local bytes with fetched data."""
    if not base_url.endswith('/'):
        base_url += '/'
    pending = dict(expected)
    received = {}
    errors = {}
    for attempt in range(attempts):
        for path in list(pending):
            url = base_url + ('' if path == 'index.html' else path)
            try:
                actual = getter(url)
                if actual != expected[path]:
                    raise ValueError('live bytes differ from local tracked output')
                received[path] = actual
                del pending[path]
                errors.pop(path, None)
            except (URLError, OSError, ValueError) as error:
                errors[path] = str(error)
        if not pending:
            break
        if attempt + 1 < attempts:
            sleeper(delay)
    if pending:
        raise RuntimeError('Live verification failed:\n' + '\n'.join(f'{path}: {errors[path]}' for path in sorted(pending)))
    print(validate_surfaces(received, records))
    print(f'Live verification: {len(received)}/{len(expected)} HTTP 200 and byte-identical')
    return received


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', required=True)
    parser.add_argument('--base-url', default=LIVE)
    parser.add_argument('--attempts', type=int, choices=range(1, 13), default=6)
    parser.add_argument('--delay', type=int, choices=range(0, 31), default=10)
    args = parser.parse_args()
    expected = render.build()
    errors = render.check(render.ROOT, expected)
    if errors:
        raise RuntimeError('\n'.join(errors))
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=render.ROOT, text=True).splitlines()
    if not set(expected) <= set(tracked):
        raise RuntimeError('Every generated output must be tracked before live verification')
    verify(args.base_url, expected, render.records(), args.attempts, args.delay)


if __name__ == '__main__':
    main()
