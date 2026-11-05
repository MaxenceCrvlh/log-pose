# Ankidō for iOS: brief for the coding agent

You are building the **native SwiftUI version of Ankidō (暗記道)**, a free kanji and Japanese vocabulary flashcard app. A working web version already exists and is the **behavior spec**: `ankido/index.html` in https://github.com/MaxenceCrvlh/log-pose (single file, vanilla JS). When anything here is ambiguous, do what the web app does.

The owner is Maxence. He studies Japanese by reading One Piece in Japanese, speaks French and English, and is not a professional iOS developer. Explain steps plainly, keep changes small, and after each step tell him exactly what to click in Xcode and what he should see.

## Environment constraints (important)
- **Intel MacBook, Xcode 26.x** (Xcode 27 needs Apple Silicon). Use only APIs available in the iOS 26 SDK.
- **Deployment target: iOS 17.0.** Gate iOS 18 and 26 APIs with `if #available`.
- Free Apple ID ("Personal Team"): device builds expire after 7 days. No iCloud or push entitlements for now.
- No third-party packages unless clearly needed. Prefer Apple frameworks.
- Nothing leaves the device: no servers, analytics or accounts. The app stays free forever.

## Data (bundle it, don't download it)
Ask Maxence to clone the repo and drag `log-pose/ankido/data/` into the Xcode project as a **folder reference** (blue folder), so `data/strokes/` keeps its structure:
```
git clone https://github.com/MaxenceCrvlh/log-pose.git ~/Developer/log-pose
```

### `data/kanji.json` (about 0.5 MB)
`{"kanji": [Kanji], "parts": {char: [englishName, frenchName]}}`. Already sorted: JLPT N5 first, then N4…N1, then non-JLPT; inside each level by frequency.
| key | meaning |
|---|---|
| `c` | the kanji (String, one character) |
| `s` | stroke count |
| `g` | school grade 1–6, 8 = secondary, 0 = none |
| `f` | frequency rank (0 = unranked) |
| `j` | JLPT level 5…1, 0 = not on JLPT |
| `m` | English meanings [String] |
| `mf` | French meanings [String] (present for all) |
| `on` | on readings in **hiragana** (display them in katakana) |
| `kun` | kun readings; `.` separates okurigana (`なが.い` → show なが + grey い), `-` marks prefix or suffix |
| `p` | optional: parts the kanji is built from (KanjiVG components) |
| `mn` | optional: memory story `[english, french]` (all 245 N5 and N4 kanji have one) |

### `data/dict.json` (about 6.8 MB): decode once, off the main thread
`{"date": String, "words": [Word]}`: about 23,000 words. JLPT words come first (N5…N1).
| key | meaning |
|---|---|
| `i` | id (String). JMdict id, or `x0`…`x72` for JLPT words not in JMdict |
| `k` | kanji spellings [String], may be empty |
| `r` | kana readings [String] |
| `s` | English senses: `[[partOfSpeech, glosses, notes]]` |
| `f` | optional French senses [String] |
| `j` | optional JLPT level |
| `h` | optional headword to display (the JLPT spelling) |
| `c` | optional 1 = common word |
| `u` | optional 1 = usually written in kana |
| `e` | optional examples `[[japanese, englishTranslation]]` (Tatoeba) |

**Headword** = `h` ?? (`u` == 1 or `k` empty ? `r[0]` : `k[0]`).
**Words containing a kanji**: index each word by the kanji in `k[0]` (or the headword). Sort by JLPT level (N5 first), then common, then length.

### `data/strokes/<hex>.json`
One file per kanji, named by its Unicode code point as 5-digit lowercase hex (`長` = `09577.json`). Content: array of SVG path `d` strings in stroke order, in a **109×109** coordinate space (KanjiVG). Write a small SVG path parser (M, m, C, c, S, s, L, l, Z) into SwiftUI `Path`, then animate each stroke with `.trim(from:to:)` one after another. Stroke number labels go near each path's first point.

## Progress and scheduling (must match the web app exactly)
Card ids: `"k" + kanjiChar` or `"v" + wordId`.

Card state (Codable; keep these exact short keys so backups stay compatible):
`i` interval in days, `e` ease, `d` due day number, `r` successful reps, `l` lapses, `n` times seen, `c` times right, `t` last review (ms since 1970), `g` last grade (1–4), optional `k` = marked known.

**Day number** (the study day rolls over at 4 am local time):
`floor((nowMs - timezoneOffsetMs - 4h) / 86_400_000)`, where local time = UTC + offset.

**Status level** (drives every color in the app):
- 0 **New**: no card state
- 1 **Weak**: last grade was 1, or interval < 1
- 2 **Learning**: interval < 7
- 3 **Good**: interval < 21
- 4 **Known**: interval ≥ 21

**Schedule** (port verbatim):
```js
function schedule(prev, g, isDueNow) {          // g: 1 Again, 2 Hard, 3 Good, 4 Easy
  const td = today();
  const c = prev ? {...prev} : {i: 0, e: 2.5, d: td, r: 0, l: 0, n: 0, c: 0};
  c.n++; if (g >= 2) c.c++;
  c.t = Date.now();
  if (!isDueNow && g >= 2 && prev && prev.i >= 1) { c.g = g; return c; }  // extra practice: a pass doesn't move the card
  if (g === 1) { if (c.r > 0 || c.i >= 1) c.l++; c.r = 0; c.i = 0; c.e = Math.max(1.3, c.e - .2); c.d = td; }
  else {
    let i;
    if (g === 2) { i = c.i < 1 ? 1 : Math.max(c.i + 1, Math.round(c.i * 1.2)); c.e = Math.max(1.3, c.e - .15); }
    else if (g === 3) { i = c.i < 1 ? 1 : c.i < 3 ? 3 : Math.round(c.i * c.e); }
    else { i = c.i < 1 ? 4 : Math.round(Math.max(c.i + 2, c.i * c.e * 1.3)); c.e += .15; }
    if (i >= 7) i = Math.round(i * (0.95 + Math.random() * .1));
    c.i = Math.min(i, 3650); c.r++; c.d = td + c.i;
  }
  c.g = g; return c;
}
```
"I know this" sets `i=60, e=2.6, d=today+60, r=max(3,r), g=4, k=1`.
Daily plan: due cards (`d <= today`, weakest first, capped by max reviews per day) plus new cards. New cards come from the "Learn next" queue first, then the selected JLPT levels in data order, up to new-per-day for kanji and for words separately. New cards are spread through the reviews. A card graded Again comes back 3–5 cards later in the same session.

### Saved state and backups
Save one Codable `Progress` value as JSON in Application Support (atomic writes). Its shape is identical to the web app's backup file, so **"Restore from file"** (`.fileImporter`) imports Maxence's existing web progress:
```
{"app":"ankido","v":1,"saved":ISO8601,"data":{
  "cards":{id:Card}, "days":{"<dayNumber>":{"r":reviews,"c":right,"nk":newKanji,"nv":newWords}},
  "my":[wordId], "notes":{id:text}, "queue":[cardId], "recent":[cardId], "ai":{kanji:{"en":..,"fr":..}},
  "set":{ newK, newV, maxRev, dirK:"k2m|m2k|mix", dirV:"j2e|e2j|mix", furi, autoSpeak, showStory, font:"sans|textbook|serif",
          theme:"auto|light|dark", lang:"en|fr", decks:["k","v"], levels:[5,4], incOther, incMine, custStatus, custCount, custOrder, group },
  "lastBackup": ms }}
```
Ignore unknown keys when decoding. "Save backup file" exports the same format (`.fileExporter` or ShareLink).

## Design (Apple HIG, native first)
Use standard components: `TabView` (Library, Study, Progress, Settings), `NavigationStack` with large titles, inset grouped `List`, `.sheet` with detents for details, `.searchable`, `Toggle`, `Stepper`, segmented `Picker`, SF Symbols, Dynamic Type, light and dark mode, VoiceOver labels.

Status colors (use these exact tones, defined as asset colors with dark variants):
| status | light | dark |
|---|---|---|
| New | #1C1C1E | #F2F2F7 |
| Weak (red) | #E5342B | #FF453A |
| Learning (yellow) | #C99400 | #FFD60A |
| Good (green) | #24963F | #30D158 |
| Known (blue) | #0A6CFF | #409CFF |
App tint: indigo **#3F4BC9** (dark: #7D87FF). Don't use blue as the tint, since blue means Known.

The app's signature element is the **practice square**: the kanji drawn in a rounded square with a dashed red cross guide (like genkō yōshi paper). It's used on flashcards, the kanji detail page and the stroke-order view. Keep everything else quiet and standard.

Japanese text uses the system font (Hiragino). Optional card fonts, Klee One (handwritten) and Shippori Mincho B1, are SIL OFL and can be bundled later.

## Screens (match the web app)
1. **Library**: today card (activity ring: done vs left today, Study button), Kanji deck card (known count, stacked mastery bar, legend, level tiles N5…N1 and Other), Vocabulary deck card (levels plus My words), recently viewed, rows for My words, Learn next queue and Backup. A toolbar button cycles Auto, Light and Dark.
2. **Kanji grid**: sections by JLPT, grade or stroke count (segmented control), each glyph colored by status, filter by status and level, search by meaning (EN and FR, accent-insensitive), reading (kana or romaji) or kanji.
3. **Vocabulary list**: segmented N5…N1 and My words, rows with the colored headword, reading and meaning.
4. **Search**: one field for English, French, kana, romaji or kanji. Returns kanji and words (port the web app's scoring).
5. **Kanji detail (sheet)**: practice square, status pill and next review, meanings, On/Kun rows, facts (JLPT, grade, strokes, frequency), **Memory aid** (parts as tappable chips with names, story in the current language, links to WaniKani, Kanji Koohii and Jisho), stroke-order animation, words using the kanji, actions (Learn next, Review now, I know this, Reset), a note field.
6. **Word detail (sheet)**: headword, reading, Listen, meanings (in French mode, French first then the English definitions), examples with the word highlighted, kanji chips, other spellings, actions, Add to my words for non-JLPT words.
7. **Study session (full screen)**: progress bar, counts, undo. Card flips with a 3D rotation on reveal. Four grade buttons show the next interval. Swipe right = Good, left = Again. Kanji cards (kanji → meaning, meaning → kanji, or mixed) show the story on the back. Word cards show senses, an example and kanji chips. The end screen shows the % right and the studied items in their new colors.
8. **Progress**: streak, cards today, cards started, 30-day accuracy, mastery per JLPT level, last 14 days chart and the next 7 days forecast (Swift Charts).
9. **Settings**: Language EN/FR, Appearance, daily limits, card direction, reading on front, read aloud, show story, card font, backup and restore, erase all, About (credits below).

### Language
English and French via a **String Catalog**. The French strings already exist in the web app's `FR` table in `index.html`: reuse them. Meanings come from `m`/`mf` and `s`/`f` depending on the language. The in-app language switch overrides the system language.

### Native features (needed for App Store review, and genuinely useful)
- `AVSpeechSynthesizer` with a ja-JP voice (Listen buttons, optional auto-read on flip)
- Haptics on reveal and grade (`.sensoryFeedback`)
- Local notification: daily reminder with the number of cards due (UserNotifications)
- Later: Home Screen widget (WidgetKit + App Group), on-device AI stories (Foundation Models, iOS 26, `#available`), on-device translation (Translation framework, iOS 17.4+)

## Build order (one step at a time; build and run after each)
1. Models and data loading (Codable, async decode, in-memory indexes), plus the progress store with import and export.
2. Library tab and the kanji grid with status colors.
3. Kanji detail sheet, including the stroke-order animation.
4. Study session, with scheduling identical to the web app.
5. Vocabulary list, search, word detail.
6. Progress and Settings, EN/FR, themes.
7. Native extras: speech, haptics, reminder notification.
8. Next big feature (see `ankido/ROADMAP.md`): the **manga reading tool**. Photograph a bubble, recognize the Japanese text (Vision), split it into words colored by mastery, tap a word for its meaning, make flashcards with the sentence and bubble image, and translate only when the user explicitly asks.

## Credits and licenses (keep these in Settings → About, on its own screen)
KANJIDIC2 and JMdict © EDRDG, CC BY-SA 4.0 (link https://www.edrdg.org/edrdg/license.html), via jmdict-simplified and kanji-data (MIT). Example sentences: Tatoeba, CC BY 2.0 FR. JLPT lists: Jonathan Waller via open-anki-jlpt-decks (MIT). Stroke order and parts: KanjiVG by Ulrich Apel, CC BY-SA 3.0. The bundled data files stay under CC BY-SA. The app code doesn't have to be open source.
