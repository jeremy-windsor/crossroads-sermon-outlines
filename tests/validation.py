"""Shared local/live validation across all generated surfaces."""

from collections import Counter
from html.parser import HTMLParser
import json
import posixpath
from urllib.parse import unquote, urlsplit, parse_qs

from bs4 import BeautifulSoup

from schema import flatten, timestamp
from templates import scripture_url, topic_membership


class StrictHTML(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []

    def handle_starttag(self, tag, attrs):
        assert len(attrs) == len({k for k, v in attrs}), f"Duplicate HTML attribute on {tag}"
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, f"Misnested closing tag: {tag}"


def validate_surfaces(surfaces, records, topics=None):
    if topics is None:
        import render
        topics = render.topics(sermon_records=records)
    by_slug = {record['slug']: record for record in records}
    topic_by_slug = topic_membership(topics)
    pages = {}
    forbidden = (
        'independent study', 'independent-study', 'not a transcript', 'not an official',
        'unofficial', 'independently prepared', 'listening and study aid',
        'original content belongs', 'sermon content belongs', 'transcript source',
        'source repository', 'ai-created', 'machine-generated',
        'this is an overview', 'detailed chronological outline', 'chronological study outline',
    )
    for path, data in surfaces.items():
        if not path.endswith(".html"):
            continue
        source = data.decode("utf-8")
        parser = StrictHTML()
        parser.feed(source)
        parser.close()
        assert not parser.stack, f"Unclosed HTML in {path}"
        soup = BeautifulSoup(source, "html.parser")
        assert source.lower().startswith("<!doctype html>")
        assert soup.html.get("lang") == "en" and soup.title and len(soup.select("h1")) == 1
        assert soup.select_one('meta[name="description"]')["content"]
        assert not soup.select("style, script[src], [style]")
        public_text = soup.get_text(" ", strip=True).lower()
        assert not [phrase for phrase in forbidden if phrase in public_text], path
        if path != 'search.html':
            assert 'search requires javascript' not in public_text
        ids = [x['id'] for x in soup.select('[id]')]
        assert len(ids) == len(set(ids)), f"Duplicate IDs in {path}"
        assert soup.select_one('.skip-link')['href'] == '#main-content'
        prefix = '../' if '/' in path else ''
        assert [x['href'] for x in soup.select('link[rel="stylesheet"]')] == [prefix + 'assets/site.css']
        assert soup.head.script and str(soup.head).index('<script>') < str(soup.head).index('rel="stylesheet"')
        assert [a.get_text(" ", strip=True) for a in soup.select('.nav-links a')] == ['Topics', 'Timeline']
        search = soup.select_one('form.site-search[role="search"]')
        assert search and search['method'] == 'get' and search['action'] == prefix + 'search.html'
        assert search.select_one('input[name="q"][type="search"]') and search.select_one('button[type="submit"]')
        assert not soup.select('.sermon-card .summary')
        listing_images = soup.select('.topic-card .topic-plate img, .sermon-card .card-plate img')
        assert [image['loading'] for image in listing_images] == ['eager'] * min(2, len(listing_images)) + ['lazy'] * max(0, len(listing_images) - 2)
        for card in soup.select('.sermon-card'):
            record = by_slug[card['data-sermon']]
            image = card.select_one('.card-plate img')
            assert image.attrs == {
                'src': f"https://i.ytimg.com/vi/{record['video_id']}/maxresdefault.jpg",
                'alt': '', 'width': '1280', 'height': '720',
                'loading': image['loading'], 'decoding': 'async',
            }
            assert card.select_one('.card-title').get_text(" ", strip=True) == record['title']
            assert card.select_one('.card-meta time')['datetime'] == record['published']
            assert record['speaker'] in card.select_one('.card-meta').get_text(" ", strip=True)
        pages[path] = soup

    assert set(pages) == {path for path in surfaces if path.endswith('.html')}
    for path, soup in pages.items():
        for node in soup.select('[href], [src]'):
            href = node.get('href', node.get('src'))
            url = urlsplit(href)
            assert not href.startswith('/'), f"Root-absolute path in {path}: {href}"
            if url.scheme:
                assert url.scheme == 'https'
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), url.path)) if url.path else path
            assert resolved in surfaces, f"Broken link in {path}: {href}"
            if url.fragment:
                assert pages[resolved].find(id=unquote(url.fragment)), f"Broken fragment in {path}: {href}"

    home = pages['index.html']
    assert not home.select('.sermon-card, .features')
    assert [x['data-topic'] for x in home.select('.topic-list .topic-card')] == [topic['id'] for topic in topics]
    latest_dates = [max(by_slug[member['slug']]['published'] for member in topic['members']) for topic in topics]
    assert latest_dates == sorted(latest_dates, reverse=True)
    assert home.h1.get_text(' ', strip=True) == 'Crossroads Sermons'

    years = sorted({r['published'][:4] for r in records}, reverse=True)
    timeline = pages['archive.html']
    assert [x['href'] for x in timeline.select('.year-list .year-link')] == [f'archive/{year}.html' for year in years]
    for year in years:
        strip = timeline.select_one(f'.year-link[href="archive/{year}.html"] + span').find_parent('p').find_next_sibling('nav')
        assert len(strip.find_all(['a', 'span'], recursive=False)) == 12
        active_months = sorted({int(record['published'][5:7]) for record in records if record['published'].startswith(year)})
        assert [a['href'] for a in strip.select('a')] == [f'archive/{year}.html#{year}-{month:02d}' for month in active_months]
        assert all(span.get('aria-hidden') == 'true' for span in strip.select('span'))
    for year in years:
        page = pages[f'archive/{year}.html']
        expected = [r for r in records if r['published'].startswith(year)]
        assert [x['data-sermon'] for x in page.select('.sermon-card')] == [r['slug'] for r in expected]
        assert [x['id'] for x in page.select('.month-section')] == sorted({r['published'][:7] for r in expected}, reverse=True)
        for section in page.select('.month-section'):
            assert all(x['data-sermon'].startswith(section['id']) for x in section.select('.sermon-card'))

    topic_index = pages['topics.html']
    assert [card['data-topic'] for card in topic_index.select('.topic-list .topic-card')] == [topic['id'] for topic in topics]
    for listing in (home, topic_index):
        for topic in topics:
            card = listing.select_one(f'.topic-card[data-topic="{topic["id"]}"]')
            destination = (f"sermons/{topic['members'][0]['slug']}.html" if len(topic['members']) == 1 else f"topics/{topic['id']}.html")
            assert card.select_one('.topic-title a')['href'] == destination
            assert 'sermon' in card.select_one('.topic-meta').get_text(' ', strip=True)
            assert 'outline' not in card.select_one('.topic-meta').get_text(' ', strip=True).lower()
    for topic in topics:
        anchor_slug = topic['anchor'] or topic['members'][0]['slug']
        anchor = by_slug[anchor_slug]
        index_card = topic_index.select_one(f'.topic-card[data-topic="{topic["id"]}"]')
        assert index_card.select_one('img')['src'] == f"https://i.ytimg.com/vi/{anchor['video_id']}/maxresdefault.jpg"
        page = pages[f"topics/{topic['id']}.html"]
        assert page.select_one('.topic-lead img')['src'] == f"https://i.ytimg.com/vi/{anchor['video_id']}/maxresdefault.jpg"
        assert [card['data-sermon'] for card in page.select('.sermon-card')] == [member['slug'] for member in topic['members']]
        assert not page.select('.topic-note')
        assert topic['note'] not in page.get_text(' ', strip=True)
        assert not page.select('.card-topic a')

    for i, record in enumerate(records):
        page = pages[f"sermons/{record['slug']}.html"]
        assert page.title.text == f"{record['title']} | Crossroads Sermons"
        assert page.iframe['src'] == f"https://www.youtube.com/embed/{record['video_id']}"
        assert page.find(id='outline-heading').get_text(' ', strip=True) == 'Overview'
        assert not page.select('.section-intro')
        assert record['section_intro'] not in page.get_text(' ', strip=True)
        assert not page.select('.notice, .ledger-intro')
        assert page.figcaption.get_text(' ', strip=True) == 'Watch on YouTube'
        labels = [item.dt.get_text(strip=True) for item in page.select('.metadata > div')]
        assert labels == ['Speaker', 'Published', 'Duration', 'Watch', 'Topic']
        nodes = list(flatten(record['movements']))
        assert [n['id'] for n in page.select('.outline-node')] == [n['id'] for n in nodes]
        assert len(page.select('tbody tr')) == len(record['ledger'])
        for node, tag in zip(nodes, page.select('.outline-node')):
            assert tag.select_one('.timestamp').text == timestamp(node['start'])
        expected_bible = Counter()
        for row in record['ledger']:
            expected_bible[scripture_url(row)] += 2
            tag = page.find(id='ledger-' + row['id'])
            assert tag['role'] == 'row' and tag.th['role'] == 'rowheader'
            assert [td['data-label'] for td in tag.select('td')] == ['Treatment', 'Timestamp', 'Spoken phrase', 'Overview section', 'YouTube', 'BibleGateway']
            assert all(td['role'] == 'cell' for td in tag.select('td'))
        assert Counter(a['href'] for a in page.select('a[href*="biblegateway.com"]')) == expected_bible
        assert page.table['role'] == 'table' and page.thead['role'] == page.tbody['role'] == 'rowgroup'
        assert all(th['role'] == 'columnheader' for th in page.select('thead th'))
        for a in page.select('a[href*="youtube.com/watch"]'):
            query = parse_qs(urlsplit(a['href']).query)
            assert query['v'] == [record['video_id']]
            if 't' in query:
                assert 0 <= int(query['t'][0].rstrip('s')) <= record['duration_seconds']
        prev, following = page.select_one('[rel="prev"]'), page.select_one('[rel="next"]')
        assert (prev['href'] if prev else None) == (records[i + 1]['slug'] + '.html' if i + 1 < len(records) else None)
        assert (following['href'] if following else None) == (records[i - 1]['slug'] + '.html' if i else None)
        assert page.select_one('.month-return')['href'] == '../archive/' + record['published'][:4] + '.html#' + record['published'][:7]
        topic, part, total = topic_by_slug[record['slug']]
        topic_row = [item for item in page.select('.metadata > div') if item.dt.get_text(strip=True) == 'Topic'][0]
        assert topic_row.a['href'] == f"../topics/{topic['id']}.html"
        assert topic_row.dd.get_text(" ", strip=True) == f"{topic['name']} · Part {part} of {total}"

    search_page = pages['search.html']
    assert search_page.select_one('#search-status[role="status"][aria-live="polite"]')
    assert search_page.select_one('#search-results[aria-label="Search results"]')
    search_script = search_page.find_all('script')[-1].string
    assert 'createElement' in search_script and 'textContent' in search_script
    assert 'innerHTML' not in search_script and 'insertAdjacentHTML' not in search_script

    index = json.loads(surfaces['search-index.json'])
    assert index['version'] == 1 and index['documents']
    expected_count = len(records) + sum(len(list(flatten(record['movements']))) + len(record['ledger']) for record in records)
    assert len(index['documents']) == expected_count
    document_urls = {document['url'] for document in index['documents']}
    for record in records:
        base = f"sermons/{record['slug']}.html"
        assert base in document_urls
        for node in flatten(record['movements']):
            assert base + '#' + node['id'] in document_urls
        for row in record['ledger']:
            assert base + '#ledger-' + row['id'] in document_urls
    for document in index['documents']:
        url = urlsplit(document['url'])
        assert url.path in pages
        if url.fragment:
            assert pages[url.path].find(id=unquote(url.fragment))
        assert not [phrase for phrase in forbidden if phrase in document['terms'].lower()]

    return f"Validated {len(pages)} HTML pages, search index, and stylesheet: HTML, links, schema, search, translations, timestamps, anchors, navigation"
