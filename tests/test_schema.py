from copy import deepcopy
import json

import pytest

import render
from schema import InvalidRecord, flatten, loads, validate, validate_series, validate_series_collection


@pytest.fixture
def record():
    return deepcopy(render.records()[0])


@pytest.fixture
def series():
    return deepcopy(render.series_records()[0])


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


def test_all_series_records_validate_with_explicit_membership():
    series_records = render.series_records()
    assert [series['id'] for series in series_records] == ['renew-me', 'by-faith']
    validate_series_collection(series_records, render.records())


@pytest.mark.parametrize('field,value', [
    ('id', 'Not A Slug'),
    ('type', 'collection'),
    ('provenance', []),
    ('members', []),
    ('anchor', '2026-01-01-missing'),
    ('description', '<b>markup</b>'),
])
def test_invalid_series_fields(series, field, value):
    series[field] = value
    with pytest.raises(InvalidRecord):
        validate_series(series)


def test_series_records_reject_duplicate_and_dangling_membership(series):
    records = render.records()
    duplicate_member = deepcopy(series)
    duplicate_member['id'] = 'duplicate-series'
    with pytest.raises(InvalidRecord, match='more than one series'):
        validate_series_collection([series, duplicate_member], records)
    duplicate_member = deepcopy(series)
    duplicate_member['members'][0]['slug'] = '2026-01-01-not-a-record'
    duplicate_member['anchor'] = duplicate_member['members'][0]['slug']
    with pytest.raises(InvalidRecord, match='Dangling'):
        validate_series_collection([duplicate_member], records)


def test_series_rejects_duplicate_member_and_duplicate_id(series):
    series['members'].append(deepcopy(series['members'][0]))
    with pytest.raises(InvalidRecord, match='Duplicate series member'):
        validate_series(series)
    first, second = deepcopy(render.series_records()[0]), deepcopy(render.series_records()[1])
    second['id'] = first['id']
    with pytest.raises(InvalidRecord, match='Duplicate series ID'):
        validate_series_collection([first, second], render.records())


def test_series_records_require_every_sermon_exactly_once():
    series_records = deepcopy(render.series_records())
    missing = series_records[0]['members'].pop()['slug']
    with pytest.raises(InvalidRecord, match='exactly one series record.*' + missing):
        validate_series_collection(series_records, render.records())


def test_series_and_member_provenance_and_standalone_shape_are_closed(series):
    series['provenance'][0]['source'] = 'theological_inference'
    with pytest.raises(InvalidRecord, match='provenance source'):
        validate_series(series)
    series = deepcopy(render.series_records()[0])
    series['type'] = 'standalone'
    with pytest.raises(InvalidRecord, match='exactly one sermon'):
        validate_series(series)
    series['members'] = series['members'][:1]
    series['anchor'] = None
    validate_series(series)
    series['members'][0]['provenance'] = []
    with pytest.raises(InvalidRecord, match='series member provenance is required'):
        validate_series(series)
    series['members'][0]['provenance'] = [{'source': 'theological_inference', 'detail': 'Not allowed.'}]
    with pytest.raises(InvalidRecord, match='series member provenance source'):
        validate_series(series)
