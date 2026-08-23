# Crossroads Sermon Outlines

A small public library of faithful chronological sermon outlines for review and Bible study after listening.

**Live site:** https://jeremy-windsor.github.io/crossroads-sermon-outlines/

## What each outline contains

- The sermon’s teaching in its original order—not a condensed summary
- Timestamped headings, supporting points, illustrations, transitions, and applications
- Every confirmed Scripture passage cited, quoted, paraphrased, or materially discussed
- A Scripture ledger with treatment, timestamp, short spoken phrase, outline location, source link, and BibleGateway NIV link

## Workflow

A sermon page is published only when the source video has a complete usable English YouTube caption track. The captions are checked for full-sermon coverage, then used to build and audit the outline. If captions are missing or incomplete, publication stops rather than silently substituting a machine transcription.

Each sermon is one self-contained HTML file. There is no site generator, content database, application framework, or separate asset pipeline.

## Published outlines

- [Inside Out — Josh Wyatt — August 16, 2026](sermons/2026-08-16-inside-out.html)

## Repository layout

```text
index.html
README.md
SKILL.md
.nojekyll
.gitignore
sermons/
  YYYY-MM-DD-sermon-slug.html
```

`SKILL.md` documents the repeatable agent workflow used to produce and verify the pages.

## Boundaries

This repository does not publish full transcripts, video/audio copies, or full NIV passage text. It does not add generated study questions, outside doctrinal commentary, or uncertain Scripture allusions. Each page links to the original sermon and labels itself as an unofficial independent study resource.
