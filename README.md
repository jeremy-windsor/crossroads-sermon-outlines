# Crossroads Sermons

Chronological sermon overviews of Crossroads Church Anthem messages, with the Bible passages each speaker names or reads. Live site: https://jeremy-windsor.github.io/crossroads-sermon-outlines/

## Two parts

- **Overviews:** one JSON record per sermon in `content/sermons/YYYY/`, plus series membership in `content/series/`. Written from the YouTube transcript by the `crossroads-sermon-outline` skill (kept in Hermes, not here).
- **Website:** `site/render.py` turns the records into static pages that GitHub Pages serves from `main`. Set and forget.

## Add a sermon

```bash
python3 site/content.py < record.json   # validate and write the record
python3 site/render.py                  # rebuild pages
make check                              # optional, takes seconds
git add -A && git commit && git push
```

New sermons appear on the site under their date and series automatically.
