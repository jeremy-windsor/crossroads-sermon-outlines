---
name: crossroads-sermon-outline
description: "Use when acquiring, verifying, and outlining Crossroads Church sermons as canonical content records."
version: 2.1.0
author: Will
license: MIT
metadata:
  hermes:
    tags: [sermons, bible-study, youtube, outlines]
---

# Crossroads Sermon Outline

## Purpose

Turn a Crossroads Church YouTube sermon into a validated canonical sermon record for review and Bible study after listening.

This is a faithful chronological overview and outline, not a condensed summary or transcript. Preserve the speaker’s order, argument, explanations, illustrations, transitions, applications, and treatment of every confirmed Bible passage. Do not add study questions, outside commentary, unrelated cross-references, model-generated tags, or theological corrections.

## Trigger and input

Use this skill when Jeremy asks for a sermon outline, asks to prepare sermon content for the outline library, or requests the latest sermon or sermons within a duration range.

Accept either:

- a direct YouTube sermon URL; or
- a relative selection request such as “the last four weekly sermons, 35–55 minutes” against the canonical channel.

For a relative request, inspect the channel’s recent uploads, exclude Shorts, livestreams, replays that are not sermons, unavailable videos, and items outside the requested duration, then take the newest qualifying number in channel order. Record the selected titles, video IDs, published dates, and durations before outlining. Do not silently substitute an older item if a newer qualifying item fails caption verification; stop on that item and report the blocker.

Normal source and scope:

- `https://youtube.com/@thecrossroadschurch`
- an English sermon video
- roughly 30–60 minutes
- complete usable original-English YouTube captions

A clearly requested exception may proceed only when its source and transcript are sound.

## Hard stops

Stop content preparation when:

- the video is unavailable, still live, or not the intended sermon;
- no complete original-English YouTube caption track exists;
- captions omit a material part of the sermon or contain unusable gaps;
- sermon or Scripture coverage cannot be verified; or
- the canonical record does not validate.

Report exactly what failed. Let Jeremy choose whether to wait, approve Whisper or another speech-to-text process, or select another sermon. Never transcribe automatically. Never construct an outline from a video description alone.

## Content workflow

### 1. Discover and verify the source

For a relative selection request, enumerate enough recent canonical-channel uploads to prove the selected set is the newest qualifying set. Apply requested duration bounds mechanically, preserve channel order, and reject non-sermon, live, unavailable, or out-of-range items before caption work.

For every selected item or direct URL, record the canonical video ID and URL, channel, title, speaker when known, published date, duration, description, live status, and available caption tracks. Confirm that the video belongs to the expected channel unless Jeremy intentionally supplied another source. Treat the description as orientation only, never as transcript evidence. Label the upload date as `published`; do not claim a preaching date without independent evidence.

### 2. Require complete captions

Use `yt-dlp` caption functions on the normal path:

- list subtitle and automatic-caption tracks;
- prefer complete manual English captions;
- otherwise use complete original-English automatic captions; and
- prefer JSON3 when available, otherwise normalize rolling VTT overlap without losing timestamps.

Verify that captions begin near the first meaningful speech, reach the last meaningful speech, agree with the video duration, and contain real original-English speech rather than placeholders or translated captions.

Keep captions, transcripts, audio, and work files outside the tracked repository. Never publish or preserve a full transcript in the canonical record.

### 3. Mark sermon boundaries

Exclude countdowns, music, dead air, and unrelated announcements. Keep opening Scripture, communion, prayer, and closing material when they materially contribute to the teaching. Record the verified sermon start and end; a new record should not invent either boundary.

### 4. Build the chronological overview and outline

Read the complete transcript before drafting. First map the sermon’s full sequence and argument; then write the overview and detailed outline from that map. Preserve the order in which the speaker develops the message. The result must support thorough after-the-fact study without replacing the original sermon.

Use the pastor’s verified first name, full name, or `Pastor <first name>` in reader-facing prose. Never refer to a pastor by surname alone. Prefer the first name in the chronological outline because it reads naturally; use full names when source identification, metadata, or ambiguity requires them. With multiple speakers sharing a first name, use full names as needed.

For each movement:

- retain its first timestamp and canonical YouTube time;
- write a concise descriptive heading;
- retain the speaker’s explanation and supporting logic;
- retain material illustrations, transitions, and applications;
- nest supporting points where the speaker does;
- attach every Scripture unit used in that movement; and
- attribute claims to the speaker instead of silently rewriting them.

Create a concise `card_summary` without weakening the detailed overview, and a distinct `section_intro` that accurately describes sermon boundaries and exclusions. Neither substitutes for reading the complete transcript or preserving the chronological argument.

### 5. Build and audit the Scripture ledger

Check the whole sermon for explicit citations, inherited chapter and verse references, direct quotations, and material paraphrases.

For every confirmed spoken unit, record:

- its canonical reference or range;
- treatment as `read/quoted`, `exposited`, or `referenced`;
- sermon timestamp;
- a short spoken quotation or identifying phrase;
- exact outline section;
- canonical timestamped YouTube link;
- BibleGateway reference and translation; and
- a brief correction note only when captions materially misstated the reference.

Use one ledger row per spoken unit or range, not one row per verse. A spoken range remains the full range. Do not reproduce full copyrighted Bible text.

Translation provenance is exact:

- use `version: NIV` and `version_source: default` when the speaker does not explicitly identify a translation;
- when the speaker names a translation for a passage or ledger unit—including NIV—use that exact version and `version_source: speaker-named`;
- apply a named translation regardless of whether treatment is `read/quoted`, `exposited`, or `referenced`;
- never infer a version from wording alone; and
- when the speaker materially compares versions, preserve the comparison in the exact outline node and record each version-specific treatment accurately.

Use encoded BibleGateway references whose decoded `reference_query` exactly equals `reference`. For example:

```text
https://www.biblegateway.com/passage/?search=Psalm%2051%3A6&version=NIV
```

Confirm references from spoken wording and context, not merely the description. For suspicious numerals, named translations, or quotations, inspect the narrow caption window and spot-check audio when necessary. Omit unresolved allusions.

Each outline node carries a unique `scripture_mentions` set of ledger IDs. Each ledger row has exactly one `anchor_node_id`: the exact node containing its spoken phrase. Multiple nodes may mention the same row; preserve those many-to-one mentions. The union of mention IDs and ledger IDs must match. Keep identifiers stable, including legacy IDs such as `OUT-01-06`, `s1.1`, and `1.1`.

After drafting, perform a second Scripture pass against the complete transcript. Search for canonical book names, chapter-and-verse language, inherited references, and distinctive biblical quotations, then inspect each candidate in context. Include references in illustrations, closing claims, prayers, and transitions. Do not promote a casual biblical-sounding phrase without contextual evidence.

### 6. Write and validate the canonical record

The executable sermon schema is `site/schema.py`. Preserve its closed key sets and accuracy rules. A canonical record includes:

- schema version, slug, title, free-text speaker, published and verified dates, duration string and seconds, canonical video ID and URL, and caption source;
- verified sermon start and end, `card_summary`, distinct `section_intro`, page metadata, disclaimer, source attribution, figcaption, and footer prose;
- chronological movements with stable node IDs, timestamp seconds, headings, ordered prose bullets, Scripture mention sets, and children no deeper than three levels; and
- every Scripture ledger row with a unique ID, canonical anchor, timestamp, treatment, short phrase, translation, required `version_source`, encoded reference, and optional correction note.

Content values are plain data: no HTML, CSS, presentation instructions, or site paths. Timestamps must be chronological, ties are permitted, and every timestamp must fall inside the video and verified sermon bounds. Curly apostrophes are the prose convention. Preserve the approved baseline fact that Keep Running’s Hebrews 12:1b row is ESV, `speaker-named`, and `exposited`; its `s2.1` node contains the spoken attribution. Other baseline NIV rows remain `default` unless their own spoken unit explicitly names NIV.

Validate candidate JSON with:

```bash
/usr/bin/python3 site/content.py --check < record.json
```

Write an approved record through the same boundary:

```bash
/usr/bin/python3 site/content.py < record.json
```

The content phase writes only `content/sermons/YYYY/*.json`. Never change existing approved sermon prose merely to satisfy presentation needs.

## Handoff boundary

Site construction and visual design are controlled separately. After content validation, hand the canonical sermon record to the existing site project; this skill does not change templates, styling, navigation, generated pages, or topic metadata.

## Completion checklist

- [ ] Canonical source, channel, metadata, duration, and live status verified.
- [ ] Complete original-English YouTube captions verified from first meaningful speech through the end.
- [ ] Sermon boundaries and the full chronological argument mapped before drafting.
- [ ] Detailed chronological overview and outline preserve explanations, illustrations, transitions, and applications.
- [ ] Every confirmed Scripture unit appears in both the outline and ledger.
- [ ] Ambiguous references and translation claims are verified or omitted.
- [ ] Canonical JSON passes the executable closed schema with all relationships intact.
- [ ] No full transcript, copied media, full copyrighted Bible text, outside commentary, site presentation change, or topic inference is included.
