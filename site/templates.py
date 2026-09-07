"""Escaped, dependency-free HTML templates. Pure functions; no filesystem access."""

from collections import defaultdict
from datetime import date
from html import escape

from schema import flatten, timestamp

CHURCH = "https://thecrossroads.church"
CHANNEL = "https://www.youtube.com/@thecrossroadschurch"
EXTERNAL = ' target="_blank" rel="noopener noreferrer"'
LABELS = ("Reference", "Treatment", "Timestamp", "Spoken phrase", "Overview section", "YouTube", "BibleGateway")
MONTHS = ("", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
MONTH_ABBREVIATIONS = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


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
    attributes = f' class="timestamp" aria-label="Watch from {timestamp(seconds)}"' if badge else ""
    return link(url, timestamp(seconds) if badge else "Watch", attributes)


def scripture_url(row):
    return f'https://www.biblegateway.com/passage/?search={row["reference_query"]}&version={row["version"]}'


def search_form(prefix):
    return f'''<form class="site-search" role="search" action="{e(prefix)}search.html" method="get">
      <label class="visually-hidden" for="site-search-query">Search sermons</label>
      <input id="site-search-query" name="q" type="search" autocomplete="off" placeholder="Search sermons or Scripture">
      <button type="submit">Search</button>
    </form>'''


def layout(title, description, prefix, header, body, scripts, current=None, extra_script=""):
    navigation = " ".join(
        link(prefix + path, label, ' aria-current="page"' if current == path else "")
        for path, label in (("index.html", "Series"), ("archive.html", "Timeline"))
    )
    footer = f'<nav aria-label="Related links">{link(CHURCH, "Crossroads Church", EXTERNAL)} {link(CHANNEL, "Crossroads Church on YouTube", EXTERNAL)}</nav>'
    search_script = f"\n  {extra_script}" if extra_script else ""
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
    {link(prefix + "index.html", "Crossroads Sermons", ' class="site-name"')}
    <div class="nav-links">{navigation}</div>
    {search_form(prefix)}
    <div class="theme-selector" role="group" aria-label="Theme" hidden><button type="button" data-theme-choice="light" aria-pressed="false">Light</button><button type="button" data-theme-choice="dark" aria-pressed="false">Dark</button><button type="button" data-theme-choice="system" aria-pressed="false">System</button></div>
  </nav>
  <header>{header}</header>
  <main id="main-content" tabindex="-1">{body}</main>
  <footer>{footer}</footer>
  <script>{scripts[1]}</script>{search_script}
</body>
</html>
'''


def series_membership(series_records):
    result = {}
    for series in series_records:
        total = len(series["members"])
        for part, member in enumerate(series["members"], start=1):
            result[member["slug"]] = (series, part, total)
    return result


def plate(record, class_name, eager=False):
    # The artwork repeats the title and speaker printed in the adjacent caption,
    # so an empty alt avoids announcing the same information twice.
    loading = "eager" if eager else "lazy"
    source = f"https://i.ytimg.com/vi/{record['video_id']}/maxresdefault.jpg"
    return f'<div class="{e(class_name)}"><img src="{e(source)}" alt="" width="1280" height="720" loading="{loading}" decoding="async"></div>'


def sermon_card(record, series_records, prefix="", heading=3, eager=False, current_series=None):
    info = series_membership(series_records).get(record["slug"])
    series_line = ""
    series_attribute = ""
    if info:
        series, part, total = info
        series_attribute = f' data-series="{e(series["id"])}"'
        if series["type"] == "standalone":
            series_line = '<p class="card-series">Standalone</p>'
        else:
            label = e(series["name"]) if current_series == series["id"] else link(prefix + "series/" + series["id"] + ".html", series["name"])
            series_line = f'<p class="card-series">{label} · {part} of {total}</p>'
    title_href = prefix + "sermons/" + record["slug"] + ".html"
    watch_link = f'<a href="{e(record["video_url"])}" aria-label="Watch {e(record["title"])} on YouTube">Watch <span aria-hidden="true">↗</span></a>'
    return f'''<article class="sermon-card" data-sermon="{e(record['slug'])}"{series_attribute}>
  {plate(record, "card-plate", eager)}
  {series_line}
  <h{heading} class="card-title">{link(title_href, record['title'])}</h{heading}>
  <p class="card-meta">{time_element(record['published'])} <span aria-hidden="true">·</span> <span>{e(record['speaker'])}</span> <span aria-hidden="true">·</span> <span>{e(record['duration'])}</span></p>
  <p class="card-watch">{watch_link}</p>
</article>'''


def sermon_grid(records, series_records, prefix="", heading=3, eager_count=2, current_series=None):
    entries = [sermon_card(record, series_records, prefix, heading, index < eager_count, current_series) for index, record in enumerate(records)]
    return '<div class="sermon-grid">' + "\n".join(entries) + "</div>"


def series_anchor(series, by_slug):
    slug = series["anchor"] or series["members"][0]["slug"]
    return by_slug[slug]


def series_period(series, by_slug):
    dates = sorted(date.fromisoformat(by_slug[member["slug"]]["published"]) for member in series["members"])
    first, last = dates[0], dates[-1]
    if (first.year, first.month) == (last.year, last.month):
        return f"{MONTHS[first.month]} {first.year}"
    if first.year == last.year:
        return f"{MONTHS[first.month]}–{MONTHS[last.month]} {first.year}"
    return f"{MONTHS[first.month]} {first.year}–{MONTHS[last.month]} {last.year}"


def series_destination(series, prefix=""):
    if series["type"] == "standalone":
        return prefix + "sermons/" + series["members"][0]["slug"] + ".html"
    return prefix + "series/" + series["id"] + ".html"


def series_card(series, by_slug, prefix="", heading=2, eager=False):
    anchor = series_anchor(series, by_slug)
    count = len(series["members"])
    destination = series_destination(series, prefix)
    link_label = "View sermon →" if series["type"] == "standalone" else "View series →"
    return f'''<article class="series-card" data-series="{e(series['id'])}">
  {plate(anchor, "series-plate", eager)}
  <div class="series-copy">
    <h{heading} class="series-title">{link(destination, series['name'])}</h{heading}>
    <p class="series-meta">{e(series['scripture_spine'])} · {count} {"sermon" if count == 1 else "sermons"} · {e(series_period(series, by_slug))}</p>
    <p class="series-description">{e(series['description'])}</p>
    <p class="series-link">{link(destination, link_label)}</p>
  </div>
</article>'''


def series_listing(records, series_records, prefix=""):
    by_slug = {record["slug"]: record for record in records}
    return '<div class="series-list">' + "\n".join(
        series_card(series, by_slug, prefix, eager=index < 2) for index, series in enumerate(series_records)
    ) + "</div>"


def home(records, series_records, scripts):
    header = '<p class="kicker">Series</p><h1>Crossroads Sermons</h1><p class="lede">Browse sermons by series, or use the Timeline to find a message by date.</p>'
    body = f'<section aria-labelledby="series-heading"><h2 id="series-heading" class="visually-hidden">Sermon series</h2>{series_listing(records, series_records)}</section>'
    return layout("Crossroads Sermons", "Browse Crossroads sermons by series, date, speaker, or Scripture reference.", "", header, body, scripts, current="index.html")


def archive(records, scripts):
    years = defaultdict(list)
    for record in records:
        years[record["published"][:4]].append(record)
    entries = []
    for year, items in sorted(years.items(), reverse=True):
        active = {int(record["published"][5:7]) for record in items}
        months = []
        for month in range(1, 13):
            if month in active:
                months.append(link(f"archive/{year}.html#{year}-{month:02d}", MONTH_ABBREVIATIONS[month], f' aria-label="{MONTHS[month]} {e(year)}"'))
            else:
                months.append(f'<span aria-hidden="true">{MONTH_ABBREVIATIONS[month]}</span>')
        month_strip = f'<nav class="month-strip" aria-label="Months with sermons in {e(year)}">{"".join(months)}</nav>'
        year_link = link("archive/" + year + ".html", year, ' class="year-link"')
        entries.append(f'<li><p class="year-head">{year_link}<span>{len(items)} sermons</span></p>{month_strip}</li>')
    body = '<ul class="year-list">' + "".join(entries) + "</ul>"
    return layout("Timeline | Crossroads Sermons", "Browse Crossroads sermons by year and month.", "", '<p class="kicker">Timeline</p><h1>Sermon timeline</h1><p class="lede">Browse by year and month to find a message.</p>', body, scripts, current="archive.html")


def year_archive(year, records, series_records, scripts):
    months = defaultdict(list)
    for record in records:
        months[record["published"][:7]].append(record)
    jump_links = " ".join(link("#" + month, MONTHS[int(month[-2:])]) for month in sorted(months, reverse=True))
    body = f'<nav class="month-nav" aria-label="Months in {year}">{jump_links}</nav>'
    seen = 0
    for month, items in sorted(months.items(), reverse=True):
        eager_count = max(0, min(2 - seen, len(items)))
        body += f'<section class="month-section" id="{e(month)}" aria-labelledby="month-{e(month)}"><h2 id="month-{e(month)}">{MONTHS[int(month[-2:])]} {e(year)}</h2>{sermon_grid(items, series_records, "../", eager_count=eager_count)}</section>'
        seen += len(items)
    header = f'<p class="kicker">{link("../archive.html", "Timeline")}</p><h1>{e(year)} sermons</h1><p class="lede">{len(records)} messages, newest first.</p>'
    return layout(f"{year} Timeline | Crossroads Sermons", f"Crossroads sermons published in {year}, grouped by month.", "../", header, body, scripts, current="archive.html")


def series_index(records, series_records, scripts):
    header = '<p class="kicker">Series</p><h1>Sermon series</h1><p class="lede">Browse sermon series and standalone messages.</p>'
    return layout("Series | Crossroads Sermons", "Browse Crossroads sermons by series.", "", header, series_listing(records, series_records), scripts, current="index.html")


def series_page(series, by_slug, series_records, scripts):
    members = [by_slug[member["slug"]] for member in series["members"]]
    anchor = series_anchor(series, by_slug)
    count = len(members)
    header = f'''<div data-series="{e(series['id'])}">
<p class="kicker">{link("../index.html", "Series")}</p>
{plate(anchor, "series-lead", True)}
<h1>{e(series['name'])}</h1>
<p class="subtitle">{e(series['scripture_spine'])} · {count} {"sermon" if count == 1 else "sermons"} · {e(series_period(series, by_slug))}</p>
<p class="lede">{e(series['description'])}</p>
</div>'''
    section_heading = "Standalone sermon" if series["type"] == "standalone" else "Sermons in this series"
    body = f'<section aria-labelledby="series-messages-heading"><h2 id="series-messages-heading">{section_heading}</h2>{sermon_grid(members, series_records, "../", current_series=series["id"])}</section>'
    return layout(f"{series['name']} | Crossroads Sermons", series["description"], "../", header, body, scripts, current="index.html")


def search(scripts, search_script):
    header = '<p class="kicker">Search</p><h1>Search sermons</h1><p class="lede">Search titles, speakers, series, Overview text, and Scripture references.</p>'
    body = '''<section class="search-page" aria-labelledby="search-results-heading">
<h2 id="search-results-heading">Results</h2>
<p class="search-help">Try a title, speaker, phrase, or reference such as “Psalm 51:10” or “Hebrews 12.”</p>
<noscript><p class="search-status">Search requires JavaScript. Browse by series or use the Timeline instead.</p></noscript>
<p id="search-status" class="search-status" role="status" aria-live="polite">Enter a search above.</p>
<ol id="search-results" class="search-results" aria-label="Search results"></ol>
</section>'''
    return layout("Search | Crossroads Sermons", "Search Crossroads sermons, series, Overview text, and Scripture references.", "", header, body, scripts, extra_script=f"<script>{search_script}</script>")


def neighbors(record, previous, following):
    links = []
    if previous:
        links.append(link(previous["slug"] + ".html", "← Previous: " + previous["title"], ' rel="prev"'))
    links.append(link('../archive/' + record['published'][:4] + '.html#' + record['published'][:7], "Return to " + MONTHS[int(record['published'][5:7])] + " " + record['published'][:4], ' class="month-return"'))
    if following:
        links.append(link(following["slug"] + ".html", "Next: " + following["title"] + " →", ' rel="next"'))
    return '<nav class="sermon-navigation" aria-label="Sermon navigation">' + " ".join(links) + "</nav>"


def sermon(record, previous, following, scripts, series_records=()):
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

    metadata = [
        ("Speaker", e(record['speaker'])),
        ("Published", time_element(record['published'])),
        ("Duration", e(record['duration'])),
        ("Watch", link(record['video_url'], 'YouTube sermon')),
    ]
    series_info = series_membership(series_records).get(record["slug"])
    series_name = "Sermon"
    if series_info and series_info[0]["type"] == "series":
        series, part, total = series_info
        series_name = series["name"]
        series_value = link("../series/" + series["id"] + ".html", series["name"]) + f" · Part {part} of {total}"
        metadata.append(("Series", series_value))
    header = f'<p class="kicker">{e(series_name)}</p><h1>{e(record["title"])}</h1><p class="subtitle">{e(record["subtitle"])}</p><dl class="metadata">' + "".join(f'<div><dt>{label}</dt><dd>{value}</dd></div>' for label, value in metadata) + "</dl>"
    body = f'''<nav class="page-sections" aria-label="On this page">{link('#outline-heading', 'Overview')}{link('#scripture-ledger', 'Scripture ledger')}</nav>
<figure class="video-block"><div class="video-shell"><iframe src="https://www.youtube.com/embed/{e(record['video_id'])}" title="{e(record['title'])} by {e(record['speaker'])} at Crossroads Church" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div><figcaption>{link(record['video_url'], 'Watch on YouTube')}</figcaption></figure>
<section aria-labelledby="outline-heading"><h2 id="outline-heading">Overview</h2>{outline(record['movements'])}</section>
<section id="scripture-ledger" class="scripture-ledger" aria-labelledby="ledger-heading"><h2 id="ledger-heading">Scripture ledger</h2>
<div class="table-wrap"><table role="table" aria-label="Scripture ledger"><caption>Scripture references in sermon order</caption><thead role="rowgroup"><tr role="row">{''.join(f'<th scope="col" role="columnheader">{label}</th>' for label in LABELS)}</tr></thead><tbody role="rowgroup">{''.join(ledger)}</tbody></table></div></section>
{neighbors(record, previous, following)}'''
    description = f"{record['title']} by {record['speaker']}, with a timestamped Overview and Scripture references."
    return layout(f"{record['title']} | Crossroads Sermons", description, "../", header, body, scripts)
