from copy import deepcopy

import pytest

import render
from validation import validate_surfaces


@pytest.mark.parametrize('old,new', [
    ('href="archive.html"', 'href="/archive.html"'),
    ('href="#main-content"', 'href="#lost-anchor"'),
    ('href="archive.html"', 'href="missing.html"'),
    ('href="assets/site.css"', 'href="assets/site.css?v=1"'),
    ('</h1>', '</h2>'),
])
def test_broken_html_or_navigation_is_rejected(old, new):
    output = render.build()
    output['index.html'] = output['index.html'].replace(old.encode(), new.encode())
    with pytest.raises(AssertionError):
        validate_surfaces(output, render.records())


@pytest.mark.parametrize('old,new', [
    ('version=ESV', 'version=NIV'),
    ('&amp;t=36s', '&amp;t=999999s'),
    ('role="table"', 'role="presentation"'),
    ('data-label="Treatment"', 'data-label="Lost"'),
    ('youtube.com/embed/F43D7jaMCqs', 'youtube.com/embed/wrong'),
])
def test_ledger_video_and_translation_regressions_are_rejected(old, new):
    output = render.build()
    path = 'sermons/2026-07-20-keep-running.html'
    assert old.encode() in output[path]
    output[path] = output[path].replace(old.encode(), new.encode())
    with pytest.raises(AssertionError):
        validate_surfaces(output, render.records())
