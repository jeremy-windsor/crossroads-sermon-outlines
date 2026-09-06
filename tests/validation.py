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


def validate_surfaces(surfaces, records):
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
    years = sorted({r['published'][:4] for r in records}, reverse=True)
    assert [x['href'] for x in pages['archive.html'].select('.year-list a')] == [f'archive/{year}.html' for year in years]
    for year in years:
        page = pages[f'archive/{year}.html']
        expected = [r for r in records if r['published'].startswith(year)]
        assert [x['data-sermon'] for x in page.select('.sermon-card')] == [r['slug'] for r in expected]
        assert [x['id'] for x in page.select('.month-section')] == sorted({r['published'][:7] for r in expected}, reverse=True)
        for section in page.select('.month-section'):
            assert all(x['data-sermon'].startswith(section['id']) for x in section.select('.sermon-card'))
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
    return f"Validated {len(pages)} HTML pages and {len(surfaces) - len(pages)} stylesheet: HTML, links, schema, translations, timestamps, anchors, navigation"
