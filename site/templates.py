"""Escaped, dependency-free HTML templates. Pure functions; no filesystem access."""

from collections import defaultdict
from datetime import date
from html import escape

from schema import flatten, timestamp

LATEST = 8
CHURCH = "https://youtube.com/@thecrossroadschurch"
REPOSITORY = "https://github.com/jeremy-windsor/crossroads-sermon-outlines"
LABELS = ("Reference", "Treatment", "Timestamp", "Spoken phrase", "Outline section", "YouTube", "BibleGateway")
MONTHS = ("", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def e(value):
    return escape(str(value), quote=True)


def date_label(value):
    day = date.fromisoformat(value)
    return f"{MONTHS[day.month]} {day.day}, {day.year}"


def time_element(value):
    return f'<time datetime="{e(value)}">{date_label(value)}</time>'


def link(href, label, attributes=""):
    return f'<a href="{e(href)}"{attributes}>{e(label)}</a>'


def watch(record, seconds, badge=True):
    url = record["video_url"] + f"&t={seconds}s"
    return link(url, timestamp(seconds) if badge else "Watch", f' class="timestamp" aria-label="Watch from {timestamp(seconds)}"' if badge else "")


def scripture_url(row):
    return f'https://www.biblegateway.com/passage/?search={row["reference_query"]}&version={row["version"]}'


def rich(parts, record):
    result = ""
    for part in parts:
        value = e(part["text"])
        if part["kind"] == "strong":
            value = f"<strong>{value}</strong>"
        elif part["kind"] == "source_link":
            value = link(record["video_url"], part["text"])
        # Keep punctuation next to its preceding link/strong segment.
        result += (" " if result and not part["text"].startswith((".", ",", ";", ":")) else "") + value
    return result


def layout(title, description, prefix, header, body, scripts, footer=None, current=None):
    navigation = " ".join(link(prefix + path, label, ' aria-current="page"' if current == path else "") for path, label in (("index.html", "Latest outlines"), ("archive.html", "Archive")))
    if footer is None:
        footer = f'<nav aria-label="Related links">{link(CHURCH, "Crossroads Church on YouTube")} {link(REPOSITORY, "Source repository")}</nav><p>This is an unofficial, independent study resource. Sermon content belongs to the original church and speaker. Scripture links open BibleGateway; NIV is the default unless the speaker names another translation.</p>'
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{e(description)}">
  <meta name="color-scheme" content="light dark">
  <title>{e(title)}</title>
  <script>{scripts[0]}</script>
  <link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to content</a>
  <nav class="site-nav" aria-label="Main navigation">
    {link(prefix + "index.html", "Crossroads / Sermon Outlines", ' class="site-name"')}
    <div class="nav-links">{navigation}</div>
    <div class="theme-controls"><button class="theme-toggle" type="button" aria-pressed="false" hidden>Dark theme</button><button class="theme-reset" type="button" hidden>Use system theme</button></div>
  </nav>
  <header>{header}</header>
  <main id="main-content" tabindex="-1">{body}</main>
  <footer>{footer}</footer>
  <script>{scripts[1]}</script>
</body>
</html>
'''


def cards(records, prefix="", heading=3):
    entries = []
    for record in records:
        entries.append(f'''<article class="sermon-card" data-sermon="{e(record['slug'])}">
  <p class="meta">Published {time_element(record['published'])}<span>{e(record['speaker'])} · {e(record['duration'])}</span></p>
  <div><h{heading}>{link(prefix + 'sermons/' + record['slug'] + '.html', record['title'])}</h{heading}>
  <p class="summary">{e(record['card_summary'])}</p></div>
</article>''')
    return '<div class="sermon-list">' + "\n".join(entries) + "</div>"


def home(records, scripts):
    header = '<p class="kicker">Independent study resource</p><h1>Crossroads<br>Sermon Outlines</h1><p class="lede">Faithful chronological outlines for reviewing sermons after listening—complete with timestamps, teaching structure, and every confirmed Scripture reference.</p>'
    body = f'''<ul class="features" aria-label="What each outline contains">
<li><strong>In order</strong>The message follows the speaker’s actual sequence.</li>
<li><strong>Timestamped</strong>Every major movement links to the original sermon.</li>
<li><strong>Scripture-audited</strong>Confirmed passages include context, treatment, source time, and a BibleGateway link.</li></ul>
<section aria-labelledby="published-heading"><div class="section-heading"><h2 id="published-heading">Latest outlines</h2>{link('archive.html', 'Browse the archive →')}</div>{cards(records[:LATEST])}</section>'''
    return layout("Crossroads Sermon Outlines", "Faithful chronological sermon outlines, timestamps, and Scripture references from Crossroads Church.", "", header, body, scripts, current="index.html")


def archive(records, scripts):
    years = defaultdict(list)
    for record in records:
        years[record["published"][:4]].append(record)
    body = '<ul class="year-list">' + "".join(f'<li>{link("archive/" + year + ".html", year)}<span>{len(items)} outlines</span></li>' for year, items in sorted(years.items(), reverse=True)) + "</ul>"
    return layout("Archive | Crossroads Sermon Outlines", "Browse sermon outlines by year and month.", "", '<p class="kicker">All outlines</p><h1>Sermon archive</h1><p class="lede">Browse by year, then follow the messages in order.</p>', body, scripts, current="archive.html")


def year_archive(year, records, scripts):
    months = defaultdict(list)
    for record in records:
        months[record["published"][:7]].append(record)
    jump_links = " ".join(link("#" + month, MONTHS[int(month[-2:])]) for month in sorted(months, reverse=True))
    body = f'<nav class="month-nav" aria-label="Months in {year}">{jump_links}</nav>'
    for month, items in sorted(months.items(), reverse=True):
        body += f'<section class="month-section" id="{month}" aria-labelledby="month-{month}"><h2 id="month-{month}">{MONTHS[int(month[-2:])]} {year}</h2>{cards(items, "../")}</section>'
    return layout(f"{year} Archive | Crossroads Sermon Outlines", f"All {year} sermon outlines, grouped by month, newest first.", "../", f'<p class="kicker">{link("../archive.html", "Sermon archive")}</p><h1>{year} outlines</h1><p class="lede">{len(records)} messages for listening, review, and Bible study.</p>', body, scripts)


def neighbors(record, previous, following):
    links = []
    if previous:
        links.append(link(previous["slug"] + ".html", "← Previous: " + previous["title"], ' rel="prev"'))
    links.append(link('../archive/' + record['published'][:4] + '.html#' + record['published'][:7], "Return to " + MONTHS[int(record['published'][5:7])] + " " + record['published'][:4], ' class="month-return"'))
    if following:
        links.append(link(following["slug"] + ".html", "Next: " + following["title"] + " →", ' rel="next"'))
    return '<nav class="sermon-navigation" aria-label="Sermon navigation">' + " ".join(links) + "</nav>"


def sermon(record, previous, following, scripts):
    rows = {row["id"]: row for row in record["ledger"]}
    nodes = {node["id"]: node for node in flatten(record["movements"])}

    def outline(items, depth=1):
        rendered = []
        for node in items:
            tags = " ".join(link('#ledger-' + sid, rows[sid]['reference'], f' class="scripture-tag" data-scripture-id="{e(sid)}"') for sid in node["scripture_mentions"])
            tags = f'<p class="scripture-links"><span>Scripture:</span> {tags}</p>' if tags else ""
            bullets = "".join(f"<li>{e(bullet)}</li>" for bullet in node["bullets"])
            child = outline(node["children"], depth + 1) if node["children"] else ""
            rendered.append(f'<li><article id="{e(node["id"])}" class="outline-node depth-{depth}"><h{depth+2}>{watch(record, node["start"])} {e(node["heading"])}</h{depth+2}>{tags}<ul>{bullets}</ul>{child}</article></li>')
        return '<ol class="' + ("outline" if depth == 1 else "outline-children") + '">' + "\n".join(rendered) + "</ol>"

    ledger = []
    for row in record["ledger"]:
        url = scripture_url(row)
        note = f'<span class="reference-note">{e(row["reference_note"])}</span>' if row["reference_note"] else ""
        values = [e(row['treatment'].capitalize()), watch(record, row['time']), f'<q>{e(row["phrase"])}</q>', link('#' + row['anchor_node_id'], nodes[row['anchor_node_id']]['heading']), watch(record, row['time'], False), link(url, row['version'])]
        cells = "".join(f'<td role="cell" data-label="{label}">{value}</td>' for label, value in zip(LABELS[1:], values))
        ledger.append(f'<tr role="row" id="ledger-{e(row["id"])}" data-scripture-id="{e(row["id"])}"><th role="rowheader" scope="row" data-label="Reference">{link(url, row["reference"])}{note}</th>{cells}</tr>')
    metadata = [("Speaker", e(record['speaker'])), ("Published", time_element(record['published'])), ("Duration", e(record['duration'])), ("Source", link(record['video_url'], 'YouTube sermon video')), ("Transcript source", e(record['caption_source'])), ("Verified", time_element(record['verified']))]
    header = f'<p class="kicker">{e(record["kicker"])}</p><h1>{e(record["title"])}</h1><p class="subtitle">{e(record["subtitle"])}</p><dl class="metadata">' + "".join(f'<div><dt>{label}</dt><dd>{value}</dd></div>' for label, value in metadata) + "</dl>"
    body = f'''<aside class="notice" aria-label="Independent study disclaimer"><p>{e(record['disclaimer'])}</p></aside>
<nav class="page-sections" aria-label="On this page">{link('#outline-heading', 'Chronological outline')}{link('#scripture-ledger', 'Scripture ledger')}</nav>
<figure class="video-block"><div class="video-shell"><iframe src="https://www.youtube.com/embed/{e(record['video_id'])}" title="{e(record['title'])} by {e(record['speaker'])} at Crossroads Church" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div><figcaption>{rich(record['figcaption'], record)}</figcaption></figure>
<section aria-labelledby="outline-heading"><h2 id="outline-heading">{e(record['outline_heading'])}</h2><p class="section-intro">{e(record['section_intro'])}</p>{outline(record['movements'])}</section>
<section id="scripture-ledger" class="scripture-ledger" aria-labelledby="ledger-heading"><h2 id="ledger-heading">{e(record['ledger_heading'])}</h2><p class="ledger-intro">{e(record['ledger_intro'])}</p>
<div class="table-wrap"><table role="table" aria-label="Scripture ledger"><caption>{e(record['ledger_caption'])}</caption><thead role="rowgroup"><tr role="row">{''.join(f'<th scope="col" role="columnheader">{label}</th>' for label in LABELS)}</tr></thead><tbody role="rowgroup">{''.join(ledger)}</tbody></table></div></section>
{neighbors(record, previous, following)}'''
    footer = "".join(f'<p>{rich(p, record)}</p>' for p in record['footer_paragraphs'])
    return layout(record['page_title'], record['description'], "../", header, body, scripts, footer)
