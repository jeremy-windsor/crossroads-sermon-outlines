---
name: crossroads-sermon-outline
description: "Use when outlining Crossroads Church sermons."
version: 1.3.1
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

The public repository stays small:

```text
index.html
README.md
SKILL.md
.nojekyll
.gitignore
sermons/YYYY-MM-DD-sermon-slug.html
```

Each sermon is one self-contained HTML file with inline CSS. Do not add a site generator, application framework, database, JSON content store, transcript archive, or separate asset tree. Root `SKILL.md` mirrors this skill.

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
- BibleGateway NIV link;
- a brief correction note only when captions materially misstated the reference.

Use one ledger row per spoken unit or range, not one row per verse. A spoken range must still be represented as the full range.

Use NIV links in this form with the reference URL-encoded:

```text
https://www.biblegateway.com/passage/?search=Psalm%2051%3A6&version=NIV
```

Do not reproduce full NIV text. Confirm passages from spoken wording and context, not merely the description. For suspicious numerals or quotations, inspect the narrow caption window and spot-check audio when necessary. Omit any unresolved allusion.

The confirmed Scripture set in the outline and ledger must match exactly. Each ledger row must link to the exact outline node containing its spoken phrase, not merely a nearby parent or related section.

After rendering, perform a second Scripture pass against the complete transcript. Search for canonical book names, chapter/verse language, inherited references, and distinctive biblical quotations, then inspect each candidate in context. This pass must catch references embedded in illustrations, closing claims, prayers, and transitions. Do not promote a casual biblical-sounding phrase to a citation without contextual evidence.

### 6. Build the sermon page

Create `sermons/YYYY-MM-DD-sermon-slug.html` containing:

- title, speaker, published date, duration, source URL, caption source, and verification date;
- metadata wording that labels an upload date as `published`, never as a verified preaching date unless the sermon date is independently established;
- embedded original YouTube video with source-link fallback;
- chronological hierarchical outline with timestamp links;
- complete Scripture ledger;
- source attribution and independent-study disclaimer;
- readable mobile-friendly inline CSS.

Do not include church logos, copied artwork, full transcripts, mirrored media, generated questions, outside commentary, or uncertain Scripture claims.

Update `index.html` with title, speaker, date, and a relative link. Keep newest entries first. Use project-relative paths such as `sermons/slug.html`; root-absolute paths break GitHub project sites.

Sync the active skill to root `SKILL.md` when it changes.

### 7. Validate and publish

Before committing, verify mechanically:

- HTML parses and required metadata exists;
- timestamps are chronological and within video duration;
- YouTube links use the correct video ID;
- NIV links contain the correct encoded reference and `version=NIV`;
- outline and ledger contain the same confirmed Scripture set;
- no unresolved allusion is presented as fact;
- no transcript, media, secret, framework output, or unrelated private data is tracked;
- index links to the exact sermon file;
- repository `SKILL.md` matches the active skill.

Require a clean or run-owned working tree, pull with `git pull --ff-only`, inspect the diff, commit, and push `main`.

A push is not proof. Fetch the live root index and sermon URL. Require HTTP 200 plus the expected title, video ID, NIV links, outline, and Scripture ledger before reporting success.

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
- [ ] One self-contained sermon HTML file and index entry created.
- [ ] No transcript, media, full NIV text, outside commentary, or secrets tracked.
- [ ] Commit and remote HEAD match.
- [ ] Live index and sermon page verified.
