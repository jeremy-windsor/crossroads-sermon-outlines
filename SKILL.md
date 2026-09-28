---
name: crossroads-sermon-outline
description: "Use when outlining or reviewing a Crossroads Church sermon from YouTube captions for the outline library."
version: 4.0.0
author: Will
license: MIT
metadata:
  hermes:
    tags: [sermons, bible-study, youtube, outlines]
---

# Crossroads Sermon Outline

Get the captions. Outline the sermon in the speaker’s order. Record every Bible passage he actually cites. Put it in one series. Publish.

An outline is a chronological study guide for someone who has listened: the speaker’s points, illustrations, transitions, and applications, in order. It is not a summary, a transcript, or commentary. No study questions, outside theology, invented cross-references, or tags.

“Do / create / outline / go get the sermon” means build **and publish** in the same turn. “What’s next / what’s missing” means inventory only: list, don’t outline.

## 1. Get the captions

Repo: `/home/claude/shared/crossroads-sermon-outlines`. Church channel: `@thecrossroadschurch`. Work files go in `/tmp/crossroads-sermon-$VIDEO_ID`, never in git.

```bash
WORKDIR=/tmp/crossroads-sermon-$VIDEO_ID; mkdir -p "$WORKDIR"
env -u PYTHONPATH yt-dlp --no-update --skip-download --write-info-json \
  --write-auto-subs --sub-langs 'en-orig,en' --sub-format json3 \
  -o "$WORKDIR/%(id)s" -- "$VIDEO_ID"
```

- Prefer `*.en-orig.json3`. No `*.json3` → stop and tell Jeremy; no Whisper, no outlining from the description.
- If Jeremy pastes the sermon text, outline that instead.
- For “the last N sermons,” list with `--flat-playlist`, skip Shorts, lives, testimonies, and announcements.
- Build a timestamped `readable.txt` and read the whole sermon once before writing.

## 2. Outline rules

- **Order:** the speaker’s order. Nest only where he nests. Maximum depth 3.
- **Start:** the first node starts at the sermon’s first spoken sentence (`sermon_start`), after music/countdown. Keep opening Scripture, prayer, communion, invitation, and closing prayer when they are part of the message.
- **Node times:** the second the section’s first sentence is spoken, not the slide or pause before it.
- **Voice:** attribute to the speaker by first name (“Josh”), or full name. Never surname alone, including “the Wyatt family.” Curly apostrophes and quotes.
- **Quotes:** only words he actually said. If captions garble a word, write the correct word silently.
- **Title:** from the YouTube title. The series name is not the sermon title.
- **Card summary:** two to four sentences on what the sermon argues, in reader prose.

## 3. Scripture rules

A passage gets a ledger row **only** if the speaker:

1. names it (book, chapter, or verse), or
2. reads or quotes it closely enough that the verse is identifiable from his words.

No row for a retold story, a theme, a doctrinal phrase (“Jesus washed feet,” “by grace through faith”), or a hymn line. When unsure, leave it out. Cite what he cited: if he says “Philippians 2,” the row is `Philippians 2`, not a verse range you picked.

- **One row per spoken unit.** A range read together is one row. Two separate uses of the same verse are two rows only if they’re in different sections; otherwise one.
- **Row time:** the second the reference or quoted words are spoken.
- **Treatment:**
  - `read/quoted` — he says the words.
  - `exposited` — he reads the passage and then teaches from it.
  - `referenced` — he names or points to it without reading it.
- **Translation:** NIV by default (`version_source: default`). Use another version only when he names it (`speaker-named`). A standing statement (“I’ll stick with the ESV throughout”) applies until he changes it. Never infer a translation from wording.
- **Phrase:** a short phrase from what he said, not full Bible text.
- **Reference note:** only when a reader needs it, e.g. “Josh says verse 13; the words are in verse 14.” Otherwise `null`.
- Every row is mentioned on the outline node where it was spoken (its `anchor_node_id`), and every mention has a row.

**Before writing:** for every row, find its words in the captions at its timestamp. If you can’t, delete the row.

## 4. No process notes

Everything in a record is published. Never write about how the outline was made: no “captions,” “transcript,” “upload,” “verified,” “omitted,” “materially paraphrased,” “the ledger,” or “recording ends.” The schema rejects these words; don’t work around it by rephrasing the same note.

## 5. Series

- The church’s YouTube **playlists** are the series list. The playlist title is the series name; the series id is its slug.
- `Watch Messages` is the full upload list, not a series. A sermon in no named playlist is **Standalone Sunday** (`type: "standalone"`).
- Clips, testimonies, Shorts, and ministry updates in a playlist are not members. If a playlist item might or might not be a sermon, ask Jeremy.
- Never create a series from topic, thumbnail art, or a shared upload date.

## 6. Write, check, publish

Copy the shape of an existing record (e.g. `content/sermons/2026/2026-08-31-crushed-joy.json`). A record holds content only: identity, `sermon_start`/`sermon_end`, `card_summary`, `movements`, `ledger`. Page chrome is generated. Do not hand the final JSON write to a subagent.

From the repo root:

```bash
env -u PYTHONPATH /usr/bin/python3 site/content.py --check < record.json   # fix until valid
env -u PYTHONPATH /usr/bin/python3 site/content.py < record.json
env -u PYTHONPATH /usr/bin/python3 site/content.py --series < series.json  # when membership changes
env -u PYTHONPATH /usr/bin/python3 site/render.py
env -u PYTHONPATH make check                                               # the only gate
git add -A && git commit -m "Add <title>" && git push
```

`make check` takes several minutes (`tests/validate.py` alone is ~75s); run it with a long timeout or in the background. Don’t run `make browser` unless Jeremy asks.

After any template/CSS change, screenshot the sermon page scrolled mid-Overview at desktop and mobile widths before pushing; `make check` does not catch overlap. After pushing, confirm `gh run list -L1` succeeds and the new page returns 200.

Don’t change templates, CSS, or navigation from this skill; site design is separate work.

## Review mode

“Review / check / audit” existing outlines is read-only until Jeremy says fix. Subagents may review in parallel (captions + record → findings list), but one agent applies every edit. Report findings by sermon: rows to remove, retimes, treatment changes, wording fixes.
