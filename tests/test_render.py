from copy import deepcopy
import io
from pathlib import Path
import shutil

import pytest
import tinycss2

from content import write_record
import render
import templates
from validation import validate_surfaces


def test_determinism_and_tracked_output():
    first, second = render.build(), render.build()
    assert first == second
    assert render.check(render.ROOT, first) == []
    assert first['assets/site.css'] == (render.ROOT / 'site/assets/site.css').read_bytes()


def test_all_generated_surfaces():
    assert 'Validated' in validate_surfaces(render.build(), render.records())


def test_renderer_reads_only_content_and_site(monkeypatch):
    real = io.open
    opened = []

    def guarded(path, mode='r', *args, **kwargs):
        path = Path(path).resolve()
        assert not any(flag in mode for flag in 'wax+')
        assert any(path.is_relative_to(render.ROOT / tree) for tree in ('content', 'site'))
        opened.append(path)
        return real(path, mode, *args, **kwargs)

    monkeypatch.setattr(io, 'open', guarded)
    render.build()
    assert len(opened) >= 12


def test_phase_write_boundaries(tmp_path, monkeypatch):
    data = render.records()[0]
    outputs = render.build()
    real = io.open
    phase = 'content'
    writes = []

    def guarded(path, mode='r', *args, **kwargs):
        path = Path(path)
        if any(flag in mode for flag in 'wax+'):
            relative = path.relative_to(tmp_path).as_posix()
            assert relative.startswith('content/sermons/') if phase == 'content' else relative in outputs
            writes.append(relative)
        return real(path, mode, *args, **kwargs)

    monkeypatch.setattr(io, 'open', guarded)
    target = write_record(tmp_path, data)
    before = target.read_bytes()
    phase = 'render'
    render.write(tmp_path, outputs)
    assert target.read_bytes() == before
    assert len(writes) == len(outputs) + 1
    assert render.check(tmp_path, outputs) == []


def test_check_catches_drift_missing_and_extra_pages(tmp_path):
    outputs = render.build()
    render.write(tmp_path, outputs)
    (tmp_path / 'index.html').write_text('manual edit')
    (tmp_path / 'assets/site.css').unlink()
    (tmp_path / 'archive/2001.html').write_text('orphan')
    assert len(render.check(tmp_path, outputs)) == 3


@pytest.mark.parametrize('path', ['content/x.json', 'site/assets/site.css', '../index.html', '/index.html', '.work/private', 'assets/extra.css'])
def test_renderer_rejects_unowned_writes(tmp_path, path):
    with pytest.raises(ValueError):
        render.write(tmp_path, {path: b'x'})


def test_symlinks_cannot_escape_phase_boundaries(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    (root / 'sermons').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        render.write(root, {'sermons/2026-01-01-example.html': b'bad'})
    (root / 'content').mkdir()
    (root / 'content/sermons').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError):
        write_record(root, render.records()[0])


def test_public_symlink_cannot_write_into_content(tmp_path):
    (tmp_path / 'content').mkdir()
    (tmp_path / 'sermons').symlink_to(tmp_path / 'content', target_is_directory=True)
    with pytest.raises(ValueError):
        render.write(tmp_path, {'sermons/2026-01-01-example.html': b'bad'})


def test_renderer_escapes_speakers_and_supports_depth_three():
    record = deepcopy(render.records()[0])
    record['speaker'] = 'Steve Coots & Students'
    child = deepcopy(record['movements'][0]['children'][0])
    child.update(id='3.1.1', scripture_mentions=[], children=[])
    record['movements'][0]['children'][0]['children'] = [child]
    result = templates.sermon(record, None, None, ('', ''))
    assert 'Steve Coots &amp; Students' in result and '<h5>' in result


def test_no_css_id_selectors_and_no_css_parse_errors():
    css = (render.ROOT / 'site/assets/site.css').read_text()

    def inspect(rules):
        for rule in rules:
            assert rule.type != 'error'
            if rule.type == 'qualified-rule':
                assert not any(token.type == 'hash' for token in rule.prelude)
            if rule.type == 'at-rule' and rule.lower_at_keyword == 'media':
                inspect(tinycss2.parse_rule_list(rule.content, skip_comments=True, skip_whitespace=True))
    inspect(tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True))


def test_future_year_and_neighbor_boundaries(tmp_path):
    (tmp_path / 'site').mkdir()
    shutil.copytree(render.ROOT / 'site/assets', tmp_path / 'site/assets')
    record = deepcopy(render.records()[0])
    for published in ['2025-12-31', '2027-01-01']:
        record['published'] = published
        record['slug'] = published + '-example'
        write_record(tmp_path, record)
    outputs = render.build(tmp_path)
    assert 'archive/2025.html' in outputs and 'archive/2027.html' in outputs
    validate_surfaces(outputs, render.records(tmp_path))
