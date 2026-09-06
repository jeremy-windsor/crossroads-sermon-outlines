from copy import deepcopy
import json

import pytest

import render
from schema import InvalidRecord, flatten, loads, validate, validate_topic, validate_topics


@pytest.fixture
def record():
    return deepcopy(render.records()[0])


@pytest.fixture
def topic():
    return deepcopy(render.topics()[0])


def test_all_records_validate_and_keep_distinct_summaries():
    for record in render.records():
        validate(record)
        assert record['card_summary'] != record['section_intro']
        assert isinstance(record['duration'], str)


@pytest.mark.parametrize('bad', ['<script>alert(1)</script>', 'x > y', '{color:red}', 'style="x"', 'assets/site.css', '../sermons/foo.html', 'color: red;'])
def test_content_rejects_presentation(record, bad):
    record['card_summary'] = bad
    with pytest.raises(InvalidRecord):
        validate(record)


@pytest.mark.parametrize('field,value', [('duration', 2940), ('duration_seconds', True), ('published', '2026-13-01'), ('slug', '../../index'), ('video_url', 'https://example.com'), ('sermon_start', -1), ('sermon_end', 999999), ('extra', 'unknown')])
def test_invalid_metadata(record, field, value):
    record[field] = value
    with pytest.raises(InvalidRecord):
        validate(record)


@pytest.mark.parametrize('field,value', [('id', 'main-content'), ('start', -1), ('start', 999999), ('start', True), ('scripture_mentions', ['SCR-999']), ('scripture_mentions', ['SCR-001', 'SCR-001']), ('bullets', [])])
def test_invalid_node(record, field, value):
    record['movements'][0][field] = value
    with pytest.raises(InvalidRecord):
        validate(record)


@pytest.mark.parametrize('field,value', [('anchor_node_id', 'missing'), ('id', 'SCR-999'), ('time', -1), ('reference_query', 'Luke%2023%3A34&version=ESV'), ('reference_query', 'wrong'), ('version', 'niv'), ('treatment', 'guessed')])
def test_invalid_ledger(record, field, value):
    record['ledger'][0][field] = value
    with pytest.raises(InvalidRecord):
        validate(record)


@pytest.mark.parametrize('version,source', [('ESV', 'default'), ('KJV', 'default'), ('NIV', 'inferred'), ('NIV', 'Speaker-named'), ('NIV', ''), ('NIV', None)])
def test_translation_provenance_rejects_invalid_or_unsupported_defaults(record, version, source):
    record['ledger'][0].update(version=version, version_source=source)
    with pytest.raises(InvalidRecord):
        validate(record)


def test_translation_provenance_is_required(record):
    del record['ledger'][0]['version_source']
    with pytest.raises(InvalidRecord, match='missing ledger fields'):
        validate(record)


@pytest.mark.parametrize('treatment', ['read/quoted', 'exposited', 'referenced'])
@pytest.mark.parametrize('version,source', [('NIV', 'default'), ('NIV', 'speaker-named'), ('ESV', 'speaker-named'), ('KJV', 'speaker-named')])
def test_translation_provenance_is_independent_of_treatment(record, treatment, version, source):
    record['ledger'][0].update(treatment=treatment, version=version, version_source=source)
    validate(record)


def test_duplicate_ids_and_disordered_timestamps(record):
    nodes = list(flatten(record['movements']))
    nodes[1]['id'] = nodes[0]['id']
    with pytest.raises(InvalidRecord):
        validate(record)
    nodes[1]['id'] = 'unique'
    nodes[1]['start'] = nodes[2]['start'] + 1
    with pytest.raises(InvalidRecord):
        validate(record)


def test_rejects_duplicate_json_keys(record):
    source = json.dumps(record).replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1')
    with pytest.raises(InvalidRecord, match='Duplicate JSON key'):
        loads(source)


def test_depth_three_and_free_text_speaker(record):
    record['speaker'] = 'Steve Coots & Students'
    child = deepcopy(record['movements'][0]['children'][0])
    child.update(id='third-depth', scripture_mentions=[], children=[])
    record['movements'][0]['children'][0]['children'] = [child]
    validate(record)
    child['children'] = [dict(child, id='too-deep', children=[])]
    with pytest.raises(InvalidRecord, match='depth'):
        validate(record)


def test_all_topics_validate_with_explicit_membership():
    topics = render.topics()
    assert [topic['id'] for topic in topics] == ['renew-me', 'by-faith']
    validate_topics(topics, render.records())


@pytest.mark.parametrize('field,value', [
    ('id', 'Not A Slug'),
    ('name_source', 'model_inferred'),
    ('members', []),
    ('anchor', '2026-01-01-missing'),
    ('description', '<b>markup</b>'),
])
def test_invalid_topic_fields(topic, field, value):
    topic[field] = value
    with pytest.raises(InvalidRecord):
        validate_topic(topic)


def test_topics_reject_duplicate_and_dangling_membership(topic):
    records = render.records()
    duplicate_member = deepcopy(topic)
    duplicate_member['id'] = 'duplicate-topic'
    with pytest.raises(InvalidRecord, match='more than one topic'):
        validate_topics([topic, duplicate_member], records)
    duplicate_member = deepcopy(topic)
    duplicate_member['members'][0]['slug'] = '2026-01-01-not-a-record'
    duplicate_member['anchor'] = duplicate_member['members'][0]['slug']
    with pytest.raises(InvalidRecord, match='Dangling'):
        validate_topics([duplicate_member], records)


def test_topic_rejects_duplicate_member_and_duplicate_id(topic):
    topic['members'].append(deepcopy(topic['members'][0]))
    with pytest.raises(InvalidRecord, match='Duplicate topic member'):
        validate_topic(topic)
    first, second = deepcopy(render.topics()[0]), deepcopy(render.topics()[1])
    second['id'] = first['id']
    with pytest.raises(InvalidRecord, match='Duplicate topic ID'):
        validate_topics([first, second], render.records())
