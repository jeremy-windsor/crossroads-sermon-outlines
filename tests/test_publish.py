import io

import pytest

import publish
import render
from verify_live import verify


def test_live_verifier_retries_only_stale_surfaces_and_validates():
    expected = render.build()
    calls = []
    sleeps = []

    def fetch(url):
        path = url.removeprefix('https://example.com/project/') or 'index.html'
        calls.append(path)
        if path == 'archive.html' and calls.count(path) == 1:
            return b'stale'
        return expected[path]

    assert verify('https://example.com/project/', expected, render.records(), 2, 0, fetch, sleeps.append) == expected
    assert len(calls) == len(expected) + 1 and sleeps == [0]


def test_live_verifier_never_accepts_different_bytes():
    with pytest.raises(RuntimeError, match='bytes differ'):
        verify('https://example.com/', {'assets/site.css': b'expected'}, [], 2, 0, lambda url: b'stale', lambda delay: None)


@pytest.mark.parametrize('branch,status', [('feature/site-redesign', ''), ('main', ' M index.html')])
def test_publisher_blocks_wrong_branch_or_uncommitted_work(branch, status):
    calls = []

    def git(*args):
        calls.append(args)
        return branch if args[0] == 'branch' else status

    with pytest.raises(RuntimeError):
        publish.publish(git, lambda *args: None)
    assert not any(args[0] in ('push', 'fetch') for args in calls)


def test_publisher_changes_only_git_refs_and_never_writes_files(monkeypatch):
    calls = []
    real = io.open

    def guarded(path, mode='r', *args, **kwargs):
        assert not any(flag in mode for flag in 'wax+')
        return real(path, mode, *args, **kwargs)

    def git(*args):
        calls.append(args)
        return {'branch': 'main', 'status': '', 'ls-files': '\n'.join(render.build()), 'rev-parse': 'same-commit'}.get(args[0], '')

    monkeypatch.setattr(io, 'open', guarded)
    verified = []
    publish.publish(git, lambda *args: verified.append(args))
    assert ('push', 'origin', 'HEAD:main') in calls
    assert ('fetch', 'origin', 'main') in calls
    assert not any(args[0] in ('add', 'commit', 'checkout', 'reset', 'merge', 'pull') for args in calls)
    assert len(verified) == 1
