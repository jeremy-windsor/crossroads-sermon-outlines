---
name: crossroads-sermon-outline
description: "Use when outlining Crossroads Church sermons."
version: 2.0.0
author: Will
license: MIT
metadata:
  hermes:
    tags: [sermons, bible-study, youtube, outlines, github-pages]
---

# Crossroads Sermon Outline

## Purpose

Turn a Crossroads Church YouTube sermon into a faithful chronological HTML outline for review and Bible study after listening. One request means one complete run: inspect, outline, audit Scripture, build, publish, and verify.

This is an outline, not a summary or transcript. Preserve the speaker's order, argument, illustrations, applications, and treatment of every confirmed Bible passage. Do not add study questions, outside commentary, unrelated cross-references, or theological corrections.

## Trigger and Input

Use when Jeremy asks for a sermon outline, asks to add a sermon to the outline site, or requests the latest sermon(s) within a duration range.

Accept either:

- a direct YouTube sermon URL; or
- a relative selection request such as “the last four weekly sermons, 35–55 minutes” against the canonical channel.

For a relative selection request, inspect the channel’s recent uploads, exclude shorts, livestreams, replays that are not sermons, unavailable videos, and items outside the requested duration, then take the newest qualifying `N` in channel order. Record the exact selected titles, video IDs, upload dates, and durations before outlining. Do not silently substitute an older item if a newer qualifying item fails caption verification; stop on that item and report the blocker.

Normal source and scope:

- `https://youtube.com/@thecrossroadschurch`
- English sermon video
- roughly 30–60 minutes
- complete usable YouTube captions

A clearly requested exception may proceed if its source and transcript are sound.

## Canonical Project

```text
Local: ${CROSSROADS_SERMON_REPO:-$HOME/shared/crossroads-sermon-outlines}
GitHub: https://github.com/jeremy-windsor/crossroads-sermon-outlines
Pages: https://jeremy-windsor.github.io/crossroads-sermon-outlines/
```

One public skill remains at root `SKILL.md`. The parent syncs it to the active Hermes skill after review; the workflow is public documentation.

```text
content/sermons/YYYY/*.json       canonical content
site/content.py                  content-only JSON writer
site/schema.py                   executable schema
site/render.py / templates.py    renderer
site/assets/site.css             shared stylesheet source
site/assets/theme*.js            inline theme script sources
site/publish.py                  publisher for committed main
index.html / archive.html        generated library navigation
archive/YYYY.html                generated month groups
sermons/YYYY-MM-DD-slug.html      generated sermon pages
assets/site.css                  deterministic stylesheet copy
tests/                           durable validation and live verifier
```

Three independently runnable phases have structural write boundaries:

| Phase | Reads | Writes only |
| --- | --- | --- |
| Content | Captions, private work, approved records | `content/sermons/YYYY/*.json` |
| Render | `content/` and `site/` | Generated HTML surfaces and `assets/site.css` |
| Publish | Committed files, Git, live HTTP | Git publication refs; no content or page edits |

Use CPython 3.13.5 at `/usr/bin/python3`, not `~/venv`. Build code has no external dependencies. `requirements-test.txt` pins extraction and test dependencies. Run `make verify` for the complete default gate and `make browser` for Chromium checks where local sockets are permitted. The restricted-environment rendered checks use the pinned test-only Node executable described in README; there is no frontend framework or site server runtime.

Do not add a database, authentication, search, a transcript archive, copied media, or external frontend dependencies. Extend the allowlist-style `.gitignore` before adding intended source trees. Temporary tests and screenshots belong in ignored `.test-artifacts/`; leave existing `.work/` and queued batch state untouched.

## Hard Stops

Stop without publishing when:

- the video is unavailable, still live, or not the intended sermon;
- no complete original-English YouTube caption track exists;
- captions omit a material part of the sermon or contain unusable gaps;
- sermon or Scripture coverage cannot be verified;
- validation fails.

Report the exact problem and let Jeremy choose whether to wait, approve Whisper/Open Speech, or select another sermon. Never run transcription automatically. Never construct an outline from the video description alone.

## Workflow

### 1. Discover or inspect the source

For a relative selection request, enumerate enough recent canonical-channel uploads to prove the selected set is the newest qualifying set. Apply the requested duration bounds mechanically, preserve channel order, and reject non-sermon or live items before caption work.

For each selected item or direct YouTube URL, record the canonical video ID and URL, channel, title, speaker when known, published date, duration, description, live status, and available caption tracks.

Confirm it belongs to the expected channel unless Jeremy intentionally supplied another source. Treat the description as orientation only, never as transcript evidence.

### 2. Require complete captions

Use `yt-dlp` caption functions only on the normal path:

- list subtitle and automatic-caption tracks;
- prefer complete manual English captions;
- otherwise use complete original-English automatic captions;
- prefer JSON3 when available; otherwise normalize rolling VTT overlap without losing timestamps.

Verify captions begin near the first meaningful speech, reach the last meaningful speech, agree with video duration, and contain real original-English speech rather than placeholders or translated captions.

Keep all caption, transcript, audio, and work files outside the tracked repository. Never publish a full transcript.

### 3. Mark sermon boundaries

Exclude countdowns, music, dead air, and unrelated announcements. Keep opening Scripture, communion, prayer, and closing material when they materially contribute to the teaching.

### 4. Build the chronological outline

Read the complete transcript before drafting. Preserve the order in which the speaker develops the sermon.

Use the pastor's verified first name, full name, or `Pastor <first name>` in reader-facing prose. Never refer to a pastor by surname alone. Prefer the first name in the chronological outline because it reads naturally; retain the full name where source identification or search metadata benefits from it. With multiple speakers sharing a first name, use full names as needed to prevent ambiguity.

For each movement:

- give its first timestamp and a timestamped YouTube link;
- write a concise descriptive heading;
- retain the speaker's explanation and supporting logic;
- retain material illustrations, transitions, and applications;
- nest supporting points where the speaker does;
- attach Scripture used in that movement;
- attribute claims to the speaker rather than silently rewriting them.

The result must support full after-the-fact study without replacing the original sermon.

### 5. Build the Scripture ledger

Check the entire sermon for explicit citations, inherited chapter/verse references, direct quotations, and material paraphrases.

For every confirmed spoken unit, record:

- canonical reference or range;
- treatment: `read/quoted`, `exposited`, or `referenced`;
- sermon timestamp;
- short spoken quotation or identifying phrase;
- exact outline section;
- timestamped YouTube link;
- BibleGateway link using the translation policy below;
- a brief correction note only when captions materially misstated the reference.

Use one ledger row per spoken unit or range, not one row per verse. A spoken range must still be represented as the full range.

Use BibleGateway links with this translation policy:

- default to `NIV` with `version_source: default` when the speaker does not explicitly identify a Bible version;
- when the speaker explicitly names a version for a passage/ledger unit—such as `ESV`, `KJV`, `NKJV`, or NIV itself—use that exact version in the row’s BibleGateway link and visible version label, and record `version_source: speaker-named`; this applies regardless of whether treatment is `read/quoted`, `exposited`, or `referenced`;
- do not infer a version from wording alone;
- when the speaker materially compares versions, preserve the comparison in the exact outline node and link each version-specific treatment accurately;
- references and paraphrases without an explicit version remain `NIV`.

Use this link form, substituting the required version code:

```text
https://www.biblegateway.com/passage/?search=Psalm%2051%3A6&version=NIV
```

Do not reproduce full copyrighted Bible text. Confirm passages from spoken wording and context, not merely the description. For suspicious numerals, named translations, or quotations, inspect the narrow caption window and spot-check audio when necessary. Omit any unresolved allusion.

Each outline node carries a `scripture_mentions` set of ledger IDs. A ledger row represents one spoken unit and has exactly one `anchor_node_id`, the exact node containing its spoken phrase. Multiple nodes may mention the same row; do not collapse those mentions into the canonical anchor. The union of mention IDs and ledger IDs must match. Keep IDs stable, including legacy `OUT-01-06`, `s1.1`, bare-digit `1.1`, and `ledger-SCR-003` anchors.

After rendering, perform a second Scripture pass against the complete transcript. Search for canonical book names, chapter/verse language, inherited references, and distinctive biblical quotations, then inspect each candidate in context. This pass must catch references embedded in illustrations, closing claims, prayers, and transitions. Do not promote a casual biblical-sounding phrase to a citation without contextual evidence.

### 6. Finish the content phase

Write a JSON record through `site/content.py` with:

- title, free-text speaker (including multiple speakers), published date, duration string and seconds, canonical video ID/URL, caption source, and verification date;
- upload dates labeled `published`; do not claim a preaching date without independent evidence;
- verified sermon start/end, `card_summary`, and the distinct `section_intro` that describes boundaries and exclusions;
- chronological movements with verbatim node IDs, timestamp seconds, headings, ordered bullets, Scripture mention sets, and children up to depth 3;
- every Scripture ledger row, its canonical anchor, translation version and required `version_source`, encoded reference, and correction/reference note where needed;
- disclaimer, source attribution, figcaption, and footer prose using plain text segments; source links use the schema’s `source_link` kind.

`site/schema.py` is the executable record contract. There is no HTML, CSS, or site path in a record. Do not hand-author page navigation. Validate stdin with `/usr/bin/python3 site/content.py --check < record.json`; write with `/usr/bin/python3 site/content.py < record.json`. Only the content tree may change in this phase.

`version_source` is exactly `default` or `speaker-named`. The schema requires NIV for `default`, and requires `speaker-named` for every non-NIV version. Explicitly named NIV also uses `speaker-named`. A named version applies to its corresponding passage/ledger unit, including units classified `exposited`, and is never inferred from similar wording. Preserve Keep Running’s Hebrews 12:1b row as ESV, `speaker-named`, and `exposited`; its published `s2.1` node supplies the explicit attribution. Other baseline NIV rows remain `default` because their published units do not explicitly name NIV. Provenance belongs to the content audit and is not displayed by the renderer. Curly apostrophes are the site typography convention; preserve all prose and identifiers.

### 7. Render and validate

Run `make render`. The renderer reads only records and site sources, escapes prose, builds latest-eight and archive navigation, adds previous/next and month-return links, preserves all anchors, and copies `site/assets/site.css` verbatim to `assets/site.css`. All generated files are tracked. Links are plain project-relative paths, including the stylesheet URL, with no query-string hash.

The shared stylesheet provides light/dark tokens, system-default/no-JS styling, mobile ledger cards with explicit table/row/rowheader/cell roles and data labels, visible focus and target indicators, and a forced-light print layout. Small inline scripts restore a saved theme before CSS loads and enable a keyboard-operable toggle plus system reset. Do not embed presentation in records or write generated pages during content work.

Run `make verify` before committing. The suite checks schema, HTML, relative links, anchors, ordered timestamps, source IDs, translation links, many-to-one Scripture relationships, phase write boundaries, deterministic output, and rendered desktop/mobile/light/dark behavior. Run `make browser` where Chromium and local HTTP sockets are available, including no-JS and keyboard navigation, theme persistence, print, responsive ledger semantics, and anchor highlighting. Keep screenshots ignored. Report any environment limitation honestly.

Migration tests always use immutable baseline `82467aea107ab7e6b51970cc5da64f827d096f87`. Never use mutable `HEAD` or rewrite/summarize migrated content to make parity pass. The nine baseline records include 488 nodes, 482 rows, 962 NIV links and 2 ESV links; Inside Out retains 111 mentions over 37 rows and its original card summary. Both summaries, correction notes, metadata, prose, timestamps, versions, and all existing IDs must survive normalized comparison. The manifest is transparently regenerated with `site/migrate.py --manifest`. That tool is a migration tool, not the normal content writer for later sermons.

Inspect `git status --ignored --short`, `git diff --check`, and the exact staged path list. Prove all intended content/site/tests/assets/archive files are tracked, and no caption, transcript, media, secret, `.work/`, screenshot, or unrelated file is staged. Do not change or sync anything outside the authorized worktree.

### 8. Publish and verify

Publication remains GitHub Pages from `main` at the repository root with `.nojekyll`. Finish the content and render phases before publication. Follow the request’s branch/review limits; a feature-branch implementation request does not authorize pushing or merging `main`.

When publication is authorized and reviewed changes are already committed on a clean `main`, run `/usr/bin/python3 site/publish.py --check`, then `/usr/bin/python3 site/publish.py --push`. The publisher does not edit, stage, commit, re-render, or repair content. It performs a normal push, fetches `origin/main`, and requires matching local/remote commits. Failures return to the owning content or render phase before a separately verified commit.

A push is not proof. `/usr/bin/python3 tests/verify_live.py --all` fetches the root, archive index, every archive year, every sermon, and shared CSS. Require HTTP 200 and byte equality with every local tracked file, then parsed title/video/count/version/anchor/timestamp/navigation assertions. The verifier retries propagation for a bounded interval and never replaces local content with live bytes. Report success only after the authorized publication is actually verified.

Rollback uses a reviewed `git revert` plus a normal push to restore prior tracked bytes; do not test rollback on the live site. No Actions pipeline, Pages source change, secrets, or tokens are part of this architecture.

## Error Handling

- **Captions missing or partial:** stop and report which tracks were checked. Offer waiting, approved transcription, or another sermon.
- **Livestream processing:** stop until the archived VOD and captions are complete.
- **Speaker or date unclear:** report only what metadata supports; label upload date as published date unless a sermon date is established.
- **Caption/reference conflict:** trust verified spoken wording and audio over caption numerals; omit if unresolved.
- **Pages failure:** inspect the deployment, repair only the publication defect, republish, and recheck live files.

## Completion Checklist

- [ ] Direct source, channel, metadata, duration, and caption tracks verified.
- [ ] Complete original-English YouTube transcript verified.
- [ ] Detailed chronological outline completed.
- [ ] Every confirmed Scripture appears in both outline and ledger.
- [ ] Ambiguous references verified or omitted.
- [ ] Validated JSON record, generated sermon, archives, homepage, and shared assets complete.
- [ ] Full suite, immutable migration parity, deterministic render check, and rendered-page checks pass.
- [ ] Content/render/publish write boundaries respected; ignored and tracked paths inspected.
- [ ] No transcript, media, full copyrighted Bible text, outside commentary, or secrets tracked.
- [ ] Commit and remote HEAD match.
- [ ] Every generated live surface returns HTTP 200 and equals local tracked bytes.
- [ ] Root public SKILL.md updated; parent handles active Hermes sync after review.
