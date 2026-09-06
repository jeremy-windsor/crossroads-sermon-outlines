#!/usr/bin/python3
"""Independent DOM parity plus reproducible extraction against a fixed Git commit."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "site"))
from bs4 import BeautifulSoup
import pytest

import migrate
import render
from schema import dumps

ROOT = migrate.ROOT
PATHS = migrate.baseline_paths()


def normalized(tag):
    return migrate.normalize(tag.get_text(" ", strip=True)) if tag else None


def snapshot(page):
    """A separate, flat DOM projection; does not call the migration extractor."""
    soup = BeautifulSoup(page, "html.parser")
    nodes = []
    for article in soup.select(".outline-node"):
        heading = article.find(["h3", "h4", "h5"], recursive=False)
        stamp = heading.a.extract()
        nodes.append({
            "id": article["id"], "depth": heading.name, "heading": normalized(heading),
            "time": (normalized(stamp), stamp["href"]),
            "bullets": [normalized(li) for li in article.find("ul", recursive=False).find_all("li", recursive=False)],
            "mentions": [(a["data-scripture-id"], normalized(a), a["href"]) for a in article.select(".scripture-tag") if a.find_parent("article") == article],
        })
    # Parse a fresh tree so extracted timestamps still participate in link parity.
    soup = BeautifulSoup(page, "html.parser")
    rows = [(row["id"], row["data-scripture-id"], [normalized(cell) for cell in row.find_all(["th", "td"], recursive=False)], [(normalized(a), a["href"]) for a in row.select("a")]) for row in soup.select("tbody tr")]
    return {
        "title": normalized(soup.title), "h1": normalized(soup.h1),
        "description": migrate.normalize(soup.select_one('meta[name="description"]')["content"]),
        "metadata": [(normalized(x.dt), normalized(x.dd), [(t.get("datetime"), normalized(t)) for t in x.select("time")], [a["href"] for a in x.select("a")]) for x in soup.select(".metadata > div")],
        "kicker": normalized(soup.select_one(".kicker")), "subtitle": normalized(soup.select_one(".subtitle")),
        "nodes": nodes, "rows": rows,
        "intro": normalized(soup.select_one(".section-intro")),
        "outline_heading": normalized(soup.find(id="outline-heading")),
        "ledger_heading": normalized(soup.find(id="scripture-ledger").h2),
        "ledger_intro": normalized(soup.find(id="scripture-ledger").p),
        "ledger_caption": normalized(soup.caption), "notice": normalized(soup.select_one(".notice")),
        "figcaption": normalized(soup.figcaption),
        "footer": [normalized(p) for p in soup.footer.find_all("p", recursive=False)],
        "iframe": (soup.iframe["src"], soup.iframe["title"]),
        "source_links": Counter(a["href"] for a in soup.select("a[href]") if urlsplit(a["href"]).scheme),
    }


def assert_parity(path):
    old = migrate.git_bytes(path)
    new = (ROOT / path).read_bytes()
    before, after = snapshot(old), snapshot(new)
    # Public chrome and process copy may change; canonical sermon content, source
    # video, outline nodes, and Scripture rows remain byte-derived from the baseline.
    for field in ("h1", "subtitle", "nodes", "rows", "iframe"):
        assert after[field] == before[field], f"{path}: changed {field}"
    before_metadata = {label: (value, times, links) for label, value, times, links in before['metadata']}
    after_metadata = {label: (value, times, links) for label, value, times, links in after['metadata']}
    for label in ('Speaker', 'Published', 'Duration'):
        assert after_metadata[label] == before_metadata[label], f"{path}: changed {label} metadata"
    assert after_metadata['Watch'][2] == before_metadata['Source'][2], f"{path}: changed source video"
    old_ids = {node['id'] for node in before['nodes']} | {row[0] for row in before['rows']}
    new_ids = {node['id'] for node in after['nodes']} | {row[0] for row in after['rows']}
    assert old_ids == new_ids, f"{path}: changed sermon anchors"
    return before


@pytest.mark.parametrize("path", PATHS)
def test_normalized_dom_parity(path):
    assert_parity(path)


def test_extraction_and_manifest_are_reproducible():
    assert len(PATHS) == 9
    assert migrate.BASELINE == "82467aea107ab7e6b51970cc5da64f827d096f87"
    assert json.loads((ROOT / "tests/migration-baseline.json").read_text()) == migrate.manifest()
    for record in migrate.extract_all():
        path = ROOT / "content/sermons/2026" / (record['slug'] + '.json')
        assert path.read_text() == dumps(record)


def test_all_nine_card_summaries_survive():
    before = BeautifulSoup(migrate.git_bytes("index.html"), "html.parser")
    records = {record['slug']: record for record in render.records()}
    for card in before.select(".sermons article"):
        slug = Path(card.select_one("h3 a")["href"]).stem
        expected = normalized(card.select_one(".summary"))
        assert migrate.normalize(records[slug]['card_summary']) == expected


def test_known_counts_and_translation_override():
    totals = Counter()
    for path in PATHS:
        soup = BeautifulSoup((ROOT / path).read_text(), "html.parser")
        totals["nodes"] += len(soup.select(".outline-node"))
        totals["rows"] += len(soup.select("tbody tr"))
        for a in soup.select('a[href*="biblegateway.com"]'):
            query = parse_qs(urlsplit(a["href"]).query)
            totals[query["version"][0]] += 1
            if query["version"] == ["ESV"]:
                assert path.endswith("keep-running.html")
                assert query["search"] == ["Hebrews 12:1b"]
        if path.endswith("inside-out.html"):
            assert len(soup.select(".scripture-tag")) == 111
            assert len(soup.select("tbody tr")) == 37
    # Direct enumeration of the immutable source corrects the review's 481/962 total.
    assert totals == Counter(nodes=488, rows=482, NIV=962, ESV=2)


def test_translation_provenance_matches_published_evidence():
    named = []
    defaults = 0
    for record in migrate.extract_all():
        for row in record['ledger']:
            if row['version_source'] == 'speaker-named':
                named.append((record['slug'], row['id'], row['reference'], row['version'], row['treatment']))
            else:
                assert row['version_source'] == 'default' and row['version'] == 'NIV'
                defaults += 1
    assert named == [('2026-07-20-keep-running', 'SCR-010', 'Hebrews 12:1b', 'ESV', 'exposited')]
    assert defaults == 481
    source = BeautifulSoup(migrate.git_bytes('sermons/2026-07-20-keep-running.html'), 'html.parser')
    assert 'Josh explicitly cites the ESV wording' in normalized(source.find(id='s2.1'))


def test_extraction_does_not_infer_named_provenance_from_a_link_alone():
    slug = '2026-07-20-keep-running'
    source = migrate.git_bytes(f'sermons/{slug}.html').decode('utf-8')
    source = source.replace('Josh explicitly cites the ESV wording', 'Josh discusses the wording')
    with pytest.raises(ValueError, match='Published translation evidence mismatch'):
        migrate.extract(source, 'Summary', slug)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", required=True, action="store_true")
    parser.parse_args()
    for path in PATHS:
        result = assert_parity(path)
        print(f"PASS {Path(path).stem}: {len(result['nodes'])} nodes, {len(result['rows'])} rows, {sum(len(n['mentions']) for n in result['nodes'])} mentions")
    test_extraction_and_manifest_are_reproducible()
    test_all_nine_card_summaries_survive()
    test_known_counts_and_translation_override()
    test_translation_provenance_matches_published_evidence()
    test_extraction_does_not_infer_named_provenance_from_a_link_alone()
    print('Translation provenance: 481 default NIV rows; 1 speaker-named ESV row (exposited)')
    print(f"Migration parity: {len(PATHS)}/{len(PATHS)} against {migrate.BASELINE}")


if __name__ == "__main__":
    main()
