# Poneglyph

Free kanji and Japanese vocabulary flashcards with spaced repetition, colored by how well you know each one.

**Your progress is not in this repository.** Everything you study is saved only on your own device (in the browser's storage).

## Install on iPhone
1. Open https://maxencecrvlh.github.io/log-pose/poneglyph/ in **Safari**.
2. Tap **Share**, then **Add to Home Screen**.
3. Open Poneglyph from its icon. It runs full-screen and works offline.

## Colors
- **Black** new: never studied
- **Red** weak: missed the last time
- **Yellow** learning: next review in under a week
- **Green** good: next review in 1–3 weeks
- **Blue** known: next review 3 weeks or more away (or marked "I know this")

## Backups
Settings → **Save backup file** → Save to Files → iCloud Drive. On a new phone, use **Restore from file**.

## Data
`data/` is built by `tools/build_data.py` from:
- [KANJIDIC2](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) via [kanji-data](https://github.com/davidluzgouveia/kanji-data): the Jōyō kanji plus every JLPT kanji
- [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) via [jmdict-simplified](https://github.com/scriptin/jmdict-simplified): common words and every JLPT word, with [Tatoeba](https://tatoeba.org) example sentences
- JLPT word lists from [open-anki-jlpt-decks](https://github.com/jamsinclair/open-anki-jlpt-decks)
- Stroke order from [KanjiVG](https://kanjivg.tagaini.net) (CC BY-SA 3.0)

KANJIDIC2 and JMdict © the Electronic Dictionary Research and Development Group, CC BY-SA 4.0.
