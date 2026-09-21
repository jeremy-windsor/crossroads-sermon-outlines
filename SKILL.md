---
name: crossroads-sermon-outline
description: "Use when outlining a Crossroads Church sermon from YouTube captions for the outline library."
version: 3.0.1
author: Will
license: MIT
metadata:
  hermes:
    tags: [sermons, bible-study, youtube, outlines]
---

# Crossroads Sermon Outline

Download the YouTube text. Outline the sermon. Hang every spoken verse on it. Assign one series. Stop.

This is a chronological outline for study after listening, not a summary and not a transcript. Keep the speaker’s order, argument, illustrations, transitions, applications, and every confirmed Bible passage. Do not add study questions, outside commentary, invented cross-references, or tags.

Publishing the website is a separate operations step. Do not render, test, or push unless Jeremy asks to put it on the site.

## Trigger

Jeremy gives a YouTube URL, pastes the sermon text, or asks for recent Crossroads sermons (`https://www.youtube.com/@thecrossroadschurch`, English, ~30–60 minutes).

If he pastes the text, skip YouTube download and outline what he pasted.

For “the last N weekly sermons,” list recent uploads with `yt-dlp --flat-playlist`, skip Shorts/lives/non-sermons, take the newest N, then outline. Inventory-only questions (what’s next, what’s missing) stay inventory-only: metadata and thumbnails, no outline.

## Get the text

Repo: `/home/claude/shared/crossroads-sermon-outlines`. Work files in `/tmp`, never in git.

Get text in one shot. Do not `--list-subs`. Do not compare caption times to duration.

```bash
WORKDIR=/tmp/crossroads-sermon-$VIDEO_ID
mkdir -p "$WORKDIR"
yt-dlp --no-update --skip-download --write-info-json \
  --write-auto-subs --sub-langs 'en-orig,en' --sub-format json3 \
  -o "$WORKDIR/%(id)s" -- "$VIDEO_ID"
```

If no `*.json3` lands, stop: no English captions. Do not Whisper. Do not outline from the description. Prefer `*.en-orig.json3` when both `en-orig` and `en` exist.

Skip countdown/music. Keep opening Scripture, prayer, communion, and closing when they are part of the teaching. Do not store a full transcript in the published record.

Do not hand the full JSON write to a subagent. Read the text and write the record yourself.

Title comes from the YouTube title when it names the message. Series name is not the sermon title. Speaker in prose: first name (Josh), never surname alone.

## Outline

Read the whole text once. Write the outline from that read.

Each movement: timestamp, heading, the point in the speaker’s order, nested only where he nested it. Attribute claims to the speaker. Curly apostrophes. NIV unless he names another translation.

## Verses

While reading, every spoken citation, quotation, or material paraphrase becomes:

- a mention on the outline node where he said it; and
- one ledger row for that spoken unit/range (not one row per verse in a range).

Omit vague allusions. Do not quote full Bible text. If he names ESV/KJV/NIV for a unit, record that version; otherwise NIV.

## Series and photo

Exactly one series, from spoken intro, YouTube title/description, thumbnail, or Jeremy. The site already uses the YouTube thumbnail (`maxresdefault`) as the photo — look at it for series branding; do not generate artwork.

No evidence of a broader series → one-member standalone series. Do not invent a series from the topic.

## Write the record, then stop

The website reads JSON, not a Word doc. Copy shape from `content/sermons/2026/2026-08-31-crushed-joy.json`. Fill it, then from the repo root:

```bash
/usr/bin/python3 site/content.py --check < record.json
/usr/bin/python3 site/content.py < record.json
```

Series file, same boundary with `--series`. If `--check` fails, fix the file. Do not explain the schema. Do not run `make verify`, WeasyPrint, pytest, or `publish.py`.

When Jeremy says publish: `python3 site/render.py`, commit, push. That is operations, not outlining.

Do not change site templates, CSS, or navigation from this skill.
