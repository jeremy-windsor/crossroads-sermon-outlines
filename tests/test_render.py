from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import subprocess

from bs4 import BeautifulSoup
import pytest
import tinycss2

from content import write_record, write_series
import render
import templates
from validation import validate_surfaces


def test_determinism_and_tracked_output():
    first, second = render.build(), render.build()
    assert first == second
    assert render.check(render.ROOT, first) == []
    assert first['assets/site.css'] == (render.ROOT / 'site/assets/site.css').read_bytes()
    assert {'search.html', 'search-index.json', 'series.html', 'series/by-faith.html', 'series/renew-me.html'} <= set(first)


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


@pytest.mark.parametrize('path', ['content/x.json', 'site/assets/site.css', '../index.html', '/index.html', '.work/private', 'assets/extra.css', 'series/not valid.html', 'series/nested/page.html'])
def test_renderer_rejects_unowned_writes(tmp_path, path):
    with pytest.raises(ValueError):
        render.write(tmp_path, {path: b'x'})


def test_renderer_allows_owned_series_outputs(tmp_path):
    outputs = {'series.html': b'index', 'series/example.html': b'detail', 'search.html': b'search', 'search-index.json': b'{}'}
    render.write(tmp_path, outputs)
    assert render.check(tmp_path, outputs) == []


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


def test_series_pages_follow_authored_order():
    records = render.records()
    series_records = deepcopy(render.series_records())
    by_slug = {record['slug']: record for record in records}
    series_records[0]['members'].reverse()
    detail = BeautifulSoup(templates.series_page(series_records[0], by_slug, series_records, ('', '')), 'html.parser')
    assert [card['data-sermon'] for card in detail.select('.sermon-card')] == [member['slug'] for member in series_records[0]['members']]


def test_series_templates_escape_reader_facing_content():
    records = render.records()
    series = deepcopy(render.series_records()[0])
    series['name'] = 'Renew & “Restore”'
    series['description'] = 'Repentance & renewal.'
    page = templates.series_page(series, {record['slug']: record for record in records}, [series], ('', ''))
    assert 'Renew &amp; “Restore”' in page
    assert 'Repentance &amp; renewal.' in page


def test_routing_uses_record_type_instead_of_member_count():
    records = render.records()
    series = deepcopy(render.series_records()[0])
    series['members'] = series['members'][:1]
    series['anchor'] = None
    by_slug = {record['slug']: record for record in records}
    card = BeautifulSoup(templates.series_card(series, by_slug), 'html.parser')
    assert card.select_one('.series-title a')['href'] == f"series/{series['id']}.html"
    assert card.select_one('.series-link a').get_text(' ', strip=True) == 'View series →'

    series['type'] = 'standalone'
    card = BeautifulSoup(templates.series_card(series, by_slug), 'html.parser')
    expected = f"sermons/{series['members'][0]['slug']}.html"
    assert card.select_one('.series-title a')['href'] == expected
    assert card.select_one('.series-link a')['href'] == expected
    assert '1 sermon' in card.select_one('.series-meta').get_text(' ', strip=True)
    detail = BeautifulSoup(templates.series_page(series, by_slug, [series], ('', '')), 'html.parser')
    assert detail.select_one('.sermon-card')['data-sermon'] == series['members'][0]['slug']
    sermon = BeautifulSoup(templates.sermon(by_slug[series['members'][0]['slug']], None, None, ('', ''), [series]), 'html.parser')
    assert not [row for row in sermon.select('.metadata > div') if row.dt.get_text(strip=True) == 'Series']
    assert sermon.select_one('.kicker').get_text(strip=True) == 'Sermon'


def test_search_index_covers_visible_content_and_exact_anchors():
    records, series_records = render.records(), render.series_records()
    index = render.search_index(records, series_records)
    documents = index['documents']
    assert len(documents) == len(records) + sum(len(list(render.flatten(record['movements']))) + len(record['ledger']) for record in records)
    by_url = {document['url']: document for document in documents}
    membership = templates.series_membership(series_records)
    for record in records:
        base = f"sermons/{record['slug']}.html"
        sermon_document = by_url[base]
        series = membership[record['slug']][0]
        for value in (record['title'], record['speaker'], record['published'], series['name']):
            assert value in sermon_document['terms']
        for node in render.flatten(record['movements']):
            document = by_url[base + '#' + node['id']]
            assert node['heading'] in document['terms']
            assert all(bullet in document['terms'] for bullet in node['bullets'])
            assert document['excerpts'] == node['bullets']
        for row in record['ledger']:
            document = by_url[base + '#ledger-' + row['id']]
            assert row['reference'] in document['terms']
            assert row['phrase'] in document['terms']
    serialized = __import__('json').dumps(index)
    assert 'Independent-study disclaimer' not in serialized
    assert 'Transcript source' not in serialized


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


def test_study_table_css_keeps_static_plate_treatment():
    css = (render.ROOT / 'site/assets/site.css').read_text()
    assert 'box-shadow: inset 0 0 0 1px var(--plate-ring)' in css
    assert '.card-title { margin: 0; font-size: 1.25rem;' in css
    assert css.count('[data-series="by-faith"]') == 3
    assert css.count('[data-series="renew-me"]') == 3
    assert 'gradient' not in css
    declarations = []
    for match in __import__('re').finditer(r'\{([^{}]*)\}', css):
        declarations.extend(tinycss2.parse_declaration_list(match.group(1), skip_comments=True, skip_whitespace=True))
    assert not {item.lower_name for item in declarations if item.type == 'declaration'} & {'animation', 'transition', 'transform'}


def test_search_focus_ring_and_compact_theme_selector_css():
    css = (render.ROOT / 'site/assets/site.css').read_text()
    assert '.site-search:focus-within { outline: 3px solid var(--focus); outline-offset: 3px;' in css
    assert '.site-search input:focus-visible, .site-search button:focus-visible { outline: none; }' in css
    assert '.theme-selector { display: inline-flex;' in css
    assert '.theme-selector button { min-height: 36px;' in css
    assert '.theme-selector button[aria-pressed="true"]' in css


def test_future_year_and_neighbor_boundaries(tmp_path):
    (tmp_path / 'site').mkdir()
    shutil.copytree(render.ROOT / 'site/assets', tmp_path / 'site/assets')
    record = deepcopy(render.records()[0])
    slugs = []
    for published in ['2025-12-31', '2027-01-01']:
        record['published'] = published
        record['slug'] = published + '-example'
        write_record(tmp_path, record)
        slugs.append(record['slug'])
    series = deepcopy(render.series_records()[0])
    series.update(id='future-series', name='Future Series', type='series', anchor=None)
    series['provenance'] = [{'source': 'jeremy_direction', 'detail': 'Test fixture series.'}]
    series['members'] = [
        {'slug': slug, 'scripture': 'Example', 'provenance': [{'source': 'jeremy_direction', 'detail': f'Jeremy assigned {slug} to Future Series.'}]}
        for slug in slugs
    ]
    series_dir = tmp_path / 'content' / 'series'
    series_dir.mkdir()
    (series_dir / 'future-series.json').write_text(json.dumps(series), encoding='utf-8')
    outputs = render.build(tmp_path)
    assert 'archive/2025.html' in outputs and 'archive/2027.html' in outputs
    records = render.records(tmp_path)
    validate_surfaces(outputs, records, render.series_records(tmp_path, records))


def test_series_content_writer_checks_candidate_and_full_collection(tmp_path):
    shutil.copytree(render.ROOT / 'content', tmp_path / 'content')
    candidate = deepcopy(render.series_records()[0])
    target = tmp_path / 'content' / 'series' / f"{candidate['id']}.json"
    before = target.read_bytes()
    candidate['members'].append(deepcopy(render.series_records()[1]['members'][0]))
    with pytest.raises(ValueError, match='more than one series record'):
        write_series(tmp_path, candidate)
    assert target.read_bytes() == before
    assert write_series(tmp_path, render.series_records()[0]) == target


def test_series_cli_check_path():
    result = subprocess.run(
        ['/usr/bin/python3', 'site/content.py', '--series', '--check'], cwd=render.ROOT,
        input=json.dumps(render.series_records()[0]), text=True, capture_output=True, check=True,
    )
    assert result.stdout == 'Valid series: renew-me\n'
