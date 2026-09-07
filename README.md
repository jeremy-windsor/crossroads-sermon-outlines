# Crossroads Sermons

A small public library of faithful chronological sermon outlines for review and Bible study after listening.

**Live site:** https://jeremy-windsor.github.io/crossroads-sermon-outlines/

## What each outline contains

- The sermon’s teaching in its original order—not a condensed summary
- Timestamped headings, supporting points, illustrations, transitions, and applications
- Every confirmed Scripture passage cited, quoted, paraphrased, or materially discussed
- A Scripture ledger with treatment, timestamp, short spoken phrase, outline location, source link, and BibleGateway passage link (NIV by default)

## Workflow

A sermon page is published only when the source video has a complete usable English YouTube caption track. The captions are checked for full-sermon coverage, then used to build and audit the outline. If captions are missing or incomplete, publication stops rather than silently substituting a machine transcription.

Sermon content lives in validated JSON records. Explicit primary-series metadata lives separately in `content/series/*.json`; every sermon must be assigned exactly once. Series identity and each sermon’s membership are recorded from spoken captions, YouTube title/description, thumbnail artwork, or Jeremy’s direction—never inferred from theology or generated tags. A sermon without a confirmed broader series receives a one-member standalone series record. A deterministic Python renderer produces the homepage, Timeline, series and sermon pages, static search index, and shared stylesheet. GitHub Pages serves the tracked repository-root files from `main` with `.nojekyll`; there is no frontend framework, database, authentication, or application server.

The homepage is the series index, sorted by each series’s newest sermon. Confirmed series open one ordered series page; standalone records link directly to their sermon while their valid series pages remain generated. The [Timeline](archive.html) links to years and active months, and [2026](archive/2026.html) groups every current sermon by month. A persistent search form opens [static search](search.html) over titles, speakers, dates, series names, all Overview headings and bullets, Scripture references, and ledger phrases. Results deep-link to the exact Overview node or Scripture-ledger row when available. Browsing works without JavaScript; only search requires it. Theme follows the system by default, and the compact Light/Dark/System selector can save an explicit preference. Printing uses the light palette.

## Published outlines

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
SKILL.md                       content acquisition, outline, and primary-series workflow
content/sermons/YYYY/*.json     canonical sermon records
content/series/*.json           explicit series membership and ordering
site/content.py                content writer (JSON on stdin)
site/schema.py                 executable record schema
site/migrate.py                immutable baseline extraction
site/render.py                 deterministic renderer and --check
site/templates.py              escaped HTML templates
site/assets/site.css           stylesheet source of truth
site/assets/theme*.js          scripts inlined by the renderer
site/assets/search.js          safe static-search script inlined on search.html
site/publish.py                publication of already-committed main
index.html                     generated series-only homepage
search.html                    generated static search interface
search-index.json              generated deterministic full-text/Scripture index
archive.html                   generated Timeline year/month directory
archive/YYYY.html              generated Timeline month groups
series.html                    generated Series directory
series/series-id.html           generated series detail and ordered messages
sermons/YYYY-MM-DD-slug.html    generated; existing URLs/IDs preserved
assets/site.css                generated verbatim stylesheet copy
tests/                         schema, parity, links, phases, rendering, live checks
```

`SKILL.md` governs source acquisition, caption verification, chronological Overview creation, Scripture-ledger audit, validated canonical sermon records, and evidence-backed primary-series assignment. It may write sermon and series JSON, but it does not change templates, styling, navigation, rendering, or publication. The root file remains the single public skill; the parent syncs it to the active Hermes skill after review.

## Build and verification

The pinned build/test interpreter is **CPython 3.13.5 at `/usr/bin/python3`**, not `~/venv`. Building uses only the Python standard library. Test and extraction dependencies (including transitive dependencies) are pinned in `requirements-test.txt`; install these into a Python 3.13.5 environment when provisioning a new machine. The sandbox-compatible rendered checks also use the installed Node.js **22.23.2** executable `/usr/bin/node` only to execute the theme scripts in an isolated test harness; it is not a site runtime.

```bash
make render
make verify
# On a machine that permits Chromium and local HTTP sockets:
/usr/bin/python3 -m playwright install chromium
make browser
```

`make verify` runs the complete default suite (including in-process rendered-page checks), migration parity, deterministic `--check`, and `git diff --check`. Tests disable unrelated pytest plugins and put temporary evidence under ignored `.test-artifacts/`. The additional `make browser` gate exercises real Chromium at 1280px and 375px, both palettes, no-JS navigation, static search and direct anchors, stored theme restoration, keyboard focus, print, and responsive ledger/search layouts. It requires local sockets and Chromium IPC. The in-process checks resolve media conditions, render the actual HTML/CSS with WeasyPrint, and execute the theme scripts with Node.

For one content record, validate or write through the content boundary:

```bash
/usr/bin/python3 site/content.py --check < record.json
/usr/bin/python3 site/content.py < record.json
make render
make verify
```

A record stores `card_summary` and `section_intro` separately. Each node has ordered prose bullets, a timestamp, verbatim ID, children (up to depth 3), and a Scripture mention set. Every ledger row has one canonical node anchor, a timestamp, short phrase, treatment, version, required `version_source`, encoded reference, and optional correction note. Many nodes may mention the same row. Timestamps permit ties and must remain chronological and within the video. `sermon_end` is nullable for migrated pages whose HTML did not state an exact endpoint; migration does not invent one. New content should record the verified endpoint.

The schema rejects HTML, CSS, site paths, unexpected fields, duplicate JSON keys, malformed dates/URLs/references, duplicate IDs, and broken mention relationships. `reference_query` preserves the original BibleGateway encoding (`+` or `%20`); decoded text must equal `reference`. `version_source` is exactly `default` or `speaker-named`: `default` requires `version: NIV`, and every non-NIV version requires `speaker-named`. An explicitly named NIV also uses `speaker-named`. Named translations apply to their corresponding passage/ledger unit regardless of treatment, including `exposited`, and must retain their spoken evidence during the content audit. The renderer does not display provenance or infer translation choice from wording.

## Migration evidence

All nine original 2026 pages and card summaries are extracted from immutable commit `82467aea107ab7e6b51970cc5da64f827d096f87`, never mutable `HEAD`. `tests/migration-baseline.json` fingerprints the original bytes and extracted records. Tests regenerate that evidence directly from Git and independently compare the old and generated DOMs after HTML unescaping, apostrophe normalization to `’`, and whitespace normalization.

```bash
# Recreate the initial records only; do not use to overwrite later editorial changes.
/usr/bin/python3 site/migrate.py --write
# Reproduce the tracked fingerprint transparently on stdout:
/usr/bin/python3 site/migrate.py --manifest
/usr/bin/python3 tests/test_migration_parity.py --all
```

The immutable source contains **488 nodes, 482 ledger rows, and 964 BibleGateway links: 962 NIV + 2 ESV**. This corrects the design review’s arithmetic (481 rows / 962 total links). Both ESV links belong to Keep Running’s Hebrews 12:1b row, whose treatment remains `exposited` and whose provenance is `speaker-named`. The published `s2.1` node explicitly attributes the ESV wording to Josh; the renderer-independent manifest records that evidence and fingerprints the extracted provenance fields. The other 481 baseline rows use `default` NIV; none has passage-specific published attribution naming NIV. Inside Out retains all **111 mention pairs across 37 rows**, including its original thin card summary. All baseline node and ledger IDs, metadata, prose, timestamps, links, summaries, and correction notes are checked. Keep the baseline commit available in clones; do not silently skip parity in a shallow clone that lacks it. An intentional later edit to these nine records needs a separately reviewed update to the migration gate; never retarget the gate to `HEAD`.

## Phase boundaries and publication

| Phase | Reads | Writes |
| --- | --- | --- |
| Content | Caption evidence, approved sermon records | `content/sermons/YYYY/*.json` through `site/content.py` |
| Series alignment | Spoken/channel/artwork/Jeremy evidence | `content/series/*.json` |
| Site structure | Approved content and site sources | `site/` |
| Render | Only `content/` and `site/` | Only generated HTML and `assets/site.css` |
| Publish | Committed files, Git, live HTTP | Git publication refs; no edits to content or pages |

Tests observe actual file operations, exercise traversal/symlink rejection, and check the publisher’s Git commands. Rendering first computes output bytes in memory. `--check` reads the generated surfaces to compare them and never writes. New directories are explicitly allowed in `.gitignore`; always inspect `git status --ignored --short` and the staged path list before committing.

After independent review, merge the feature branch to `main`, run `make verify`, and commit the complete generated output. Only when publication is authorized:

```bash
/usr/bin/python3 site/publish.py --check
/usr/bin/python3 site/publish.py --push
# Re-run independently after deployment:
/usr/bin/python3 tests/verify_live.py --all
```

The publisher requires clean, committed `main`, pushes without force, fetches `origin/main`, requires matching commits, and checks every generated surface. Live verification requires HTTP 200 **and byte equality** with every local tracked file, followed by parsed HTML, title, video, counts, translation, timestamp, anchor, archive, and neighbor assertions. Retries are bounded (`--attempts 6 --delay 10` by default). `--base-url` can target a local project-prefix preview. Verification never changes files to match live bytes.

Deployment stays branch-root from `main`; no Pages reconfiguration or Actions build is needed. Rollback is a reviewed `git revert` of the published change followed by a normal push, restoring the previously tracked bytes. Do not exercise rollback on the live site merely to test it. The plain relative stylesheet URL has no query-string hash; a cached stylesheet can remain visible until the Pages cache expires, as approved.

## Boundaries

This repository does not publish full transcripts, video/audio copies, or full copyrighted Bible text. It does not add generated study questions, outside doctrinal commentary, uncertain Scripture allusions, or series tags inferred from theology. Each sermon page retains the embedded video, direct Watch link, timestamped Overview, and Scripture ledger.
