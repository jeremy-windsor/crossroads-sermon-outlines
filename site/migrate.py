#!/usr/bin/python3
"""Mechanical extraction from the immutable pre-redesign Git commit, never HEAD.

BeautifulSoup is used only for migration/tests. No captions or work files are read.
--write writes only content records. --manifest prints reproducible evidence to stdout.
"""

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup, NavigableString

from content import write_record
from schema import SCHEMA_VERSION, dumps, seconds, validate

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "82467aea107ab7e6b51970cc5da64f827d096f87"
# Passage-specific attribution in the immutable published outline. A link's version
# code alone is not evidence that the speaker named it. No baseline unit names NIV.
SPEAKER_NAMED_UNITS = {
    "2026-07-20-keep-running": {
        "SCR-010": {
            "reference": "Hebrews 12:1b",
            "version": "ESV",
            "anchor_node_id": "s2.1",
            "evidence": "Josh explicitly cites the ESV wording",
        },
    },
}


def normalize(value):
    return " ".join(html.unescape(value).replace("'", "’").split())


def node_text(tag):
    return normalize(tag.get_text(" ", strip=True))


def git_bytes(path):
    return subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)


def baseline_paths():
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE, "sermons/"], cwd=ROOT, text=True).splitlines()
    return sorted(path for path in paths if re.fullmatch(r"sermons/2026-\d\d-\d\d-[a-z0-9-]+\.html", path))


def rich_text(tag):
    parts = []
    for child in tag.children:
        if isinstance(child, NavigableString):
            kind, value = "text", normalize(str(child))
        else:
            if child.name not in ("strong", "a"):
                raise ValueError(f"Unrecognized prose element: {child.name}")
            kind, value = ("source_link" if child.name == "a" else "strong"), node_text(child)
        if value:
            parts.append({"kind": kind, "text": value})
    return parts


def time_link(tag):
    return int(parse_qs(urlsplit(tag["href"]).query)["t"][0].rstrip("s"))


def version_source(soup, slug, row):
    attribution = SPEAKER_NAMED_UNITS.get(slug, {}).get(row["id"])
    if attribution is None:
        return "default"
    anchor = soup.find(id=attribution["anchor_node_id"])
    if (any(row[key] != attribution[key] for key in ("reference", "version", "anchor_node_id"))
            or anchor is None or attribution["evidence"] not in node_text(anchor)):
        raise ValueError(f"Published translation evidence mismatch: {slug}/{row['id']}")
    return "speaker-named"


def extract(page, card_summary, slug):
    soup = BeautifulSoup(page, "html.parser")
    metadata = {node_text(x.dt): x.dd for x in soup.select(".metadata > div")}
    video_url = metadata["Source"].a["href"]

    def movement(article):
        heading = article.find(re.compile(r"^h[3-5]$"), recursive=False)
        title = normalize(" ".join(str(x) for x in heading.contents if isinstance(x, NavigableString)))
        child_list = article.find("ol", recursive=False)
        scripture = article.find("p", class_="scripture-links", recursive=False)
        return {
            "id": article["id"], "start": time_link(heading.a), "heading": title,
            "scripture_mentions": [a["data-scripture-id"] for a in scripture.select(".scripture-tag")] if scripture else [],
            "bullets": [node_text(li) for li in article.find("ul", recursive=False).find_all("li", recursive=False)],
            "children": [movement(li.find("article", recursive=False)) for li in child_list.find_all("li", recursive=False)] if child_list else [],
        }

    ledger = []
    for row in soup.select("tbody tr"):
        cells = row.find_all("td", recursive=False)
        reference = row.th.a
        query = urlsplit(reference["href"]).query
        entry = {
            "id": row["data-scripture-id"], "reference": node_text(reference),
            "reference_query": re.search(r"(?:^|&)search=([^&]+)", query)[1],
            "treatment": node_text(cells[0]).lower(), "time": time_link(cells[1].a),
            "phrase": node_text(cells[2].q), "anchor_node_id": cells[3].a["href"][1:],
            "version": parse_qs(query)["version"][0],
        }
        entry["version_source"] = version_source(soup, slug, entry)
        entry["reference_note"] = node_text(row.select_one(".reference-note")) if row.select_one(".reference-note") else None
        ledger.append(entry)
    movements = [movement(li.find("article", recursive=False)) for li in soup.select_one("ol.outline").find_all("li", recursive=False)]
    intro = node_text(soup.select_one(".section-intro"))
    end = re.search(r"continues through the closing prayer at (\d+:\d\d)", intro)
    ledger_section = soup.find(id="scripture-ledger")
    record = {
        "schema_version": SCHEMA_VERSION, "slug": slug, "title": node_text(soup.h1),
        "speaker": node_text(metadata["Speaker"]), "published": metadata["Published"].time["datetime"],
        "duration": node_text(metadata["Duration"]), "duration_seconds": seconds(node_text(metadata["Duration"])),
        "video_id": parse_qs(urlsplit(video_url).query)["v"][0], "video_url": video_url,
        "caption_source": node_text(metadata["Transcript source"]), "verified": metadata["Verified"].time["datetime"],
        "sermon_start": movements[0]["start"], "sermon_end": seconds(end[1]) if end else None,
        "card_summary": normalize(card_summary), "section_intro": intro,
        "page_title": node_text(soup.title), "description": normalize(soup.select_one('meta[name="description"]')["content"]),
        "subtitle": node_text(soup.select_one(".subtitle")), "kicker": node_text(soup.select_one(".kicker")),
        "disclaimer": node_text(soup.select_one(".notice")), "figcaption": rich_text(soup.figcaption),
        "footer_paragraphs": [rich_text(p) for p in soup.footer.find_all("p", recursive=False)],
        "outline_heading": node_text(soup.find(id="outline-heading")),
        "ledger_heading": node_text(ledger_section.h2), "ledger_intro": node_text(ledger_section.p),
        "ledger_caption": node_text(ledger_section.caption), "movements": movements, "ledger": ledger,
    }
    return validate(record)


def extract_all():
    index = BeautifulSoup(git_bytes("index.html"), "html.parser")
    summaries = {a.select_one("h3 a")["href"]: node_text(a.select_one(".summary")) for a in index.select(".sermons article")}
    return [extract(git_bytes(path), summaries[path], Path(path).stem) for path in baseline_paths()]


def manifest():
    records = extract_all()
    return {
        "baseline_commit": BASELINE,
        "normalization": "HTML unescape; straight apostrophe to curly apostrophe; collapse whitespace; strip",
        "speaker_named_units": SPEAKER_NAMED_UNITS,
        "sources": {path: hashlib.sha256(git_bytes(path)).hexdigest() for path in ["index.html", *baseline_paths()]},
        "records": {r["slug"]: hashlib.sha256(dumps(r).encode()).hexdigest() for r in records},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--manifest", action="store_true")
    args = parser.parse_args()
    if args.manifest:
        print(json.dumps(manifest(), indent=2) + "\n", end="")
    else:
        records = extract_all()
        for record in records:
            write_record(ROOT, record)
        print(f"Extracted {len(records)}/{len(baseline_paths())} sermons from {BASELINE}")


if __name__ == "__main__":
    main()
