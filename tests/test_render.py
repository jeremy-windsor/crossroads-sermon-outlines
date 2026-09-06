from copy import deepcopy
import io
import json
from pathlib import Path
import shutil

from bs4 import BeautifulSoup
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
    assert {'search.html', 'search-index.json', 'topics.html', 'topics/by-faith.html', 'topics/renew-me.html'} <= set(first)


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


@pytest.mark.parametrize('path', ['content/x.json', 'site/assets/site.css', '../index.html', '/index.html', '.work/private', 'assets/extra.css', 'topics/not valid.html', 'topics/nested/page.html', 'series/old-name.html'])
def test_renderer_rejects_unowned_writes(tmp_path, path):
    with pytest.raises(ValueError):
        render.write(tmp_path, {path: b'x'})


def test_renderer_allows_owned_topic_outputs(tmp_path):
    outputs = {'topics.html': b'index', 'topics/example.html': b'detail', 'search.html': b'search', 'search-index.json': b'{}'}
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


def test_topic_pages_follow_authored_order():
    records = render.records()
    topics = deepcopy(render.topics())
    by_slug = {record['slug']: record for record in records}
    topics[0]['members'].reverse()
    detail = BeautifulSoup(templates.topic_page(topics[0], by_slug, topics, ('', '')), 'html.parser')
    assert [card['data-sermon'] for card in detail.select('.sermon-card')] == [member['slug'] for member in topics[0]['members']]


def test_topic_templates_escape_reader_facing_content():
    records = render.records()
    topic = deepcopy(render.topics()[0])
    topic['name'] = 'Renew & “Restore”'
    topic['description'] = 'Repentance & renewal.'
    page = templates.topic_page(topic, {record['slug']: record for record in records}, [topic], ('', ''))
    assert 'Renew &amp; “Restore”' in page
    assert 'Repentance &amp; renewal.' in page


def test_single_member_topic_card_links_directly_but_detail_remains_supported():
    records = render.records()
    topic = deepcopy(render.topics()[0])
    topic['type'] = 'standalone'
    topic['members'] = topic['members'][:1]
    topic['anchor'] = None
    by_slug = {record['slug']: record for record in records}
    card = BeautifulSoup(templates.topic_card(topic, by_slug), 'html.parser')
    expected = f"sermons/{topic['members'][0]['slug']}.html"
    assert card.select_one('.topic-title a')['href'] == expected
    assert card.select_one('.topic-link a')['href'] == expected
    assert '1 sermon' in card.select_one('.topic-meta').get_text(' ', strip=True)
    detail = BeautifulSoup(templates.topic_page(topic, by_slug, [topic], ('', '')), 'html.parser')
    assert detail.select_one('.sermon-card')['data-sermon'] == topic['members'][0]['slug']


def test_search_index_covers_visible_content_and_exact_anchors():
    records, topics = render.records(), render.topics()
    index = render.search_index(records, topics)
    documents = index['documents']
    assert len(documents) == len(records) + sum(len(list(render.flatten(record['movements']))) + len(record['ledger']) for record in records)
    by_url = {document['url']: document for document in documents}
    membership = templates.topic_membership(topics)
    for record in records:
        base = f"sermons/{record['slug']}.html"
        sermon_document = by_url[base]
        topic = membership[record['slug']][0]
        for value in (record['title'], record['speaker'], record['published'], topic['name']):
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
    assert css.count('[data-topic="by-faith"]') == 3
    assert css.count('[data-topic="renew-me"]') == 3
    assert 'gradient' not in css
    declarations = []
    for match in __import__('re').finditer(r'\{([^{}]*)\}', css):
        declarations.extend(tinycss2.parse_declaration_list(match.group(1), skip_comments=True, skip_whitespace=True))
    assert not {item.lower_name for item in declarations if item.type == 'declaration'} & {'animation', 'transition', 'transform'}


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
    topic = deepcopy(render.topics()[0])
    topic.update(id='future-series', name='Future Series', type='series', anchor=None)
    topic['provenance'] = [{'source': 'jeremy_direction', 'detail': 'Test fixture topic.'}]
    topic['members'] = [{'slug': slug, 'scripture': 'Example'} for slug in slugs]
    topic_dir = tmp_path / 'content' / 'topics'
    topic_dir.mkdir()
    (topic_dir / 'future-series.json').write_text(json.dumps(topic), encoding='utf-8')
    outputs = render.build(tmp_path)
    assert 'archive/2025.html' in outputs and 'archive/2027.html' in outputs
    records = render.records(tmp_path)
    validate_surfaces(outputs, records, render.topics(tmp_path, records))
