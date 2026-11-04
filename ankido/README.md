# Ankidō 暗記道

*Anki* (暗記) means memorizing in Japanese; *-dō* (道) is "the way", as in jūdō. Free kanji and Japanese vocabulary flashcards with spaced repetition, in English or French, colored by how well you know each one.

**Your progress is not in this repository.** Everything you study is saved only on your own device (in the browser's storage).

## Install on iPhone
1. Open https://maxencecrvlh.github.io/log-pose/ankido/ in **Safari**.
2. Tap **Share**, then **Add to Home Screen**.
3. Open Ankidō from its icon. It runs full-screen and works offline.

(The old address, `/log-pose/poneglyph/`, forwards here, and your progress carries over.)

## Colors
- **Black** new: never studied
- **Red** weak: missed last time
- **Yellow** learning: next review in under a week
- **Green** good: next review in 1–3 weeks
- **Blue** known: next review 3 weeks or more away (or marked "I know this")

## Memory aids
Every kanji shows the parts it's built from. The 245 JLPT N5 and N4 kanji have an original memory story in English and French. For any other kanji, you can have Claude write one (Settings → Memory stories with Claude, with your own Anthropic API key, kept on the phone), write your own, or open WaniKani, Kanji Koohii or Jisho.

## Backups
Settings → **Save backup file** → Save to Files → iCloud Drive. On a new phone, use **Restore from file**.

## Data
`data/` is built by `tools/build_data.py` from:
- [KANJIDIC2](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) (English via [kanji-data](https://github.com/davidluzgouveia/kanji-data), French via [jmdict-simplified](https://github.com/scriptin/jmdict-simplified)): the Jōyō kanji plus every JLPT kanji
- [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) via jmdict-simplified: common words and every JLPT word, English and French glosses, [Tatoeba](https://tatoeba.org) example sentences
- JLPT word lists from [open-anki-jlpt-decks](https://github.com/jamsinclair/open-anki-jlpt-decks)
- Stroke order and kanji parts from [KanjiVG](https://kanjivg.tagaini.net) (CC BY-SA 3.0)
- `tools/fr_kanji_extra.tsv`, `tools/fr_words_extra.tsv`: French written for this app where the dictionaries have none
- `tools/mnemonics.tsv`: the memory stories; `tools/radicals.tsv`: names of the parts that aren't kanji

KANJIDIC2 and JMdict © the Electronic Dictionary Research and Development Group, CC BY-SA 4.0.
