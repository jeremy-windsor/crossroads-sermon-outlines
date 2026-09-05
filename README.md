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

- [Crushed Joy — Josh Wyatt — August 31, 2026](sermons/2026-08-31-crushed-joy.html)
- [Start With Me — Josh Wyatt — August 24, 2026](sermons/2026-08-24-start-with-me.html)
- [Inside Out — Josh Wyatt — August 16, 2026](sermons/2026-08-16-inside-out.html)
- [Born Bent — Elijah Stanley — August 10, 2026](sermons/2026-08-10-born-bent.html)
- [When Excuses Die — Josh Wyatt — August 3, 2026](sermons/2026-08-03-when-excuses-die.html)
- [Family Resemblance — Josh Wyatt — July 27, 2026](sermons/2026-07-27-family-resemblance.html)
- [Keep Running! — Josh Wyatt — July 20, 2026](sermons/2026-07-20-keep-running.html)

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
