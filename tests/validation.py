"""Shared local/live validation across all generated HTML and CSS surfaces."""

from collections import Counter
from html.parser import HTMLParser
import posixpath
from urllib.parse import unquote, urlsplit, parse_qs

from bs4 import BeautifulSoup

from schema import flatten, timestamp
from templates import LATEST, scripture_url


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
    topic_by_slug = {
        member['slug']: (topic, part, len(topic['members']))
        for topic in topics
        for part, member in enumerate(topic['members'], start=1)
    }
    pages = {}
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
        assert not __import__('re').search(r"\b(?:AI|AI-created|machine-generated)\b", soup.get_text(" "))
        ids = [x['id'] for x in soup.select('[id]')]
        assert len(ids) == len(set(ids)), f"Duplicate IDs in {path}"
        assert soup.select_one('.skip-link')['href'] == '#main-content'
        prefix = '../' if '/' in path else ''
        assert [x['href'] for x in soup.select('link[rel="stylesheet"]')] == [prefix + 'assets/site.css']
        assert soup.head.script and str(soup.head).index('<script>') < str(soup.head).index('rel="stylesheet"')
        assert [a.get_text(" ", strip=True) for a in soup.select('.nav-links a')] == ['Home', 'Topics', 'Timeline']
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
    for path, soup in pages.items():
        for a in soup.select('[href], [src]'):
            href = a.get('href', a.get('src'))
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
    assert [x['data-sermon'] for x in home.select('.sermon-card')] == [r['slug'] for r in records[:LATEST]]
    assert home.main.find_all(recursive=False)[-1].get('class') == ['features']
    assert [x['data-topic'] for x in home.select('.topic-grid .topic-card')] == [topic['id'] for topic in topics]
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
    grouped = set(topic_by_slug)
    standalone = [record['slug'] for record in records if record['slug'] not in grouped]
    assert [card['data-sermon'] for card in topic_index.select('.standalone .sermon-card')] == standalone
    for topic in topics:
        anchor_slug = topic['anchor'] or topic['members'][0]['slug']
        anchor = by_slug[anchor_slug]
        index_card = topic_index.select_one(f'.topic-card[data-topic="{topic["id"]}"]')
        assert index_card.select_one('img')['src'] == f"https://i.ytimg.com/vi/{anchor['video_id']}/maxresdefault.jpg"
        page = pages[f"topics/{topic['id']}.html"]
        assert page.select_one('.topic-lead img')['src'] == f"https://i.ytimg.com/vi/{anchor['video_id']}/maxresdefault.jpg"
        assert [card['data-sermon'] for card in page.select('.sermon-card')] == [member['slug'] for member in topic['members']]
        assert page.select_one('.topic-note') and topic['note'] in page.select_one('.topic-note').get_text(" ", strip=True)
        assert not page.select('.card-topic a')
    for i, record in enumerate(records):
        page = pages[f"sermons/{record['slug']}.html"]
        assert page.title.text == record['page_title']
        assert page.iframe['src'] == f"https://www.youtube.com/embed/{record['video_id']}"
        nodes = list(flatten(record['movements']))
        assert [n['id'] for n in page.select('.outline-node')] == [n['id'] for n in nodes]
        assert len(page.select('tbody tr')) == len(record['ledger'])
        for node, tag in zip(nodes, page.select('.outline-node')):
            assert tag.select_one('.timestamp').text == timestamp(node['start'])
        expected_bible = Counter({})
        for row in record['ledger']:
            expected_bible[scripture_url(row)] += 2
            tag = page.find(id='ledger-' + row['id'])
            assert tag['role'] == 'row' and tag.th['role'] == 'rowheader'
            assert [td['data-label'] for td in tag.select('td')] == ['Treatment', 'Timestamp', 'Spoken phrase', 'Outline section', 'YouTube', 'BibleGateway']
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
        topic_info = topic_by_slug.get(record['slug'])
        topic_rows = [item for item in page.select('.metadata > div') if item.dt.get_text(strip=True) == 'Topic']
        if topic_info:
            topic, part, total = topic_info
            assert len(topic_rows) == 1
            assert topic_rows[0].a['href'] == f"../topics/{topic['id']}.html"
            assert topic_rows[0].dd.get_text(" ", strip=True) == f"{topic['name']} · Part {part} of {total}"
        else:
            assert not topic_rows
    return f"Validated {len(pages)} HTML pages and {len(surfaces) - len(pages)} stylesheet: HTML, links, schema, translations, timestamps, anchors, navigation"
