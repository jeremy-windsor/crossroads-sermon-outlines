# Crossroads Sermons

A small public library of faithful chronological sermon outlines for review and Bible study after listening.

**Live site:** https://jeremy-windsor.github.io/crossroads-sermon-outlines/

## What each outline contains

- The sermon’s teaching in its original order—not a condensed summary
- Timestamped headings, supporting points, illustrations, transitions, and applications
- Every Scripture passage the speaker names, reads, or clearly quotes
- A Scripture ledger with treatment, timestamp, short spoken phrase, outline location, source link, and BibleGateway passage link (NIV by default)

## Workflow

Outlines are written from the video’s English YouTube captions. No captions, no outline; there is no machine-transcription fallback.

Each sermon is one JSON record in `content/sermons/YYYY/`. Series membership lives in `content/series/*.json`, and every sermon belongs to exactly one series or standalone record. Membership comes from the church’s YouTube playlists (or Jeremy’s direction), never from topic. A Python renderer turns the records into static pages; GitHub Pages serves `main`.

## Published outlines

- [So That You May Know — Josh Wyatt — September 14, 2026](sermons/2026-09-14-so-that-you-may-know.html)
- [Renew US — Josh Wyatt — September 8, 2026](sermons/2026-09-08-renew-us.html)
- [Crushed Joy — Josh Wyatt — August 31, 2026](sermons/2026-08-31-crushed-joy.html)
- [Start With Me — Josh Wyatt — August 24, 2026](sermons/2026-08-24-start-with-me.html)
- [Inside Out — Josh Wyatt — August 16, 2026](sermons/2026-08-16-inside-out.html)
- [Born Bent — Elijah Stanley — August 10, 2026](sermons/2026-08-10-born-bent.html)
- [When Excuses Die — Josh Wyatt — August 3, 2026](sermons/2026-08-03-when-excuses-die.html)
- [Family Resemblance — Josh Wyatt — July 27, 2026](sermons/2026-07-27-family-resemblance.html)
- [Keep Running! — Josh Wyatt — July 20, 2026](sermons/2026-07-20-keep-running.html)
- [Walk By Faith — Josh Wyatt — July 13, 2026](sermons/2026-07-13-walk-by-faith.html)
- [Worship in the Waiting — Elijah Stanley — July 6, 2026](sermons/2026-07-06-worship-in-the-waiting.html)
- [The New and Living Way — Josh Wyatt — June 29, 2026](sermons/2026-06-29-the-new-and-living-way.html)
- [Tetelestai — Josh Wyatt — June 22, 2026](sermons/2026-06-22-tetelestai.html)
- [The Way In — Josh Wyatt — June 15, 2026](sermons/2026-06-15-the-way-in.html)
- [Anchored Heavenward — Josh Wyatt — June 8, 2026](sermons/2026-06-08-anchored-heavenward.html)
- [Too Old for Milk — Josh Wyatt — June 1, 2026](sermons/2026-06-01-too-old-for-milk.html)
- [Our Great High Priest — Steve Coots, Caleb Bromley & Levi Cuevas — May 27, 2026](sermons/2026-05-27-our-great-high-priest.html)
- [Enter His Rest — Josh Wyatt — May 17, 2026](sermons/2026-05-17-enter-his-rest.html)
- [We See Jesus — Josh Wyatt — May 11, 2026](sermons/2026-05-11-we-see-jesus.html)
- [Preeminent — Josh Wyatt — May 4, 2026](sermons/2026-05-04-preeminent.html)

## Repository layout

```text
SKILL.md                        outline workflow and rules
content/sermons/YYYY/*.json     sermon records (content only)
content/series/*.json           series membership and order
site/schema.py                  record rules, including the reader-text check
site/content.py                 validate/write a record (JSON on stdin)
site/render.py                  renderer; --check compares output to tracked pages
site/templates.py               HTML templates (page chrome lives here, not in records)
site/assets/                    stylesheet and scripts (source of truth)
index.html, archive*, series*, sermons/, search*   generated output
tests/                          schema, render, link, and page validation
```

## Records

A record holds only sermon content: identity (slug, title, speaker, date, video), sermon start/end, a card summary, the outline (`movements`), and the Scripture ledger. Headings, subtitles, footers, counts, and disclaimers are generated, so no process notes can be stored in a record.

The schema rejects:

- unknown or missing fields, HTML/CSS, and malformed dates, URLs, or references;
- outline or ledger timestamps out of order or outside the video;
- outline mentions that don’t match ledger rows;
- a non-NIV translation unless marked `speaker-named`;
- process wording in reader text (captions, transcript, upload, “materially…”, “verified”, and similar);
- the speaker referred to by surname alone.

## Build and check

Use `/usr/bin/python3` (CPython 3.13.5). The build needs only the standard library; test dependencies are in `requirements-test.txt`. If the shell has `PYTHONPATH` set by another tool, clear it (`env -u PYTHONPATH make check`).

```bash
/usr/bin/python3 site/content.py --check < record.json   # validate one record
/usr/bin/python3 site/content.py < record.json           # write it
make render                                              # rebuild pages
make check                                               # publish gate
```

`make check` is the only gate: render check, page validation, unit tests, and `git diff --check`. `make browser` (Chromium layout checks) and `make verify-live` (compare GitHub Pages to local bytes) are optional.

Publish by committing to `main` and pushing. Pages deploys from the repository root.

## Boundaries

No full transcripts, video/audio copies, or full copyrighted Bible text. No study questions, outside commentary, uncertain Scripture allusions, or topic tags. Every sermon page keeps the embedded video, Watch link, timestamped Overview, and Scripture ledger.
