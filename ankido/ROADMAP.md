# Ankidō roadmap

Notes from planning conversations, kept here so nothing gets lost. Nothing below is built yet unless it says so.

## Direction
- The app stays **free forever**, with no ads, no account and no tracking. Everything runs on the phone, so there are no server costs. The only cost is Apple's developer fee ($99/year).
- Next big step: a **native SwiftUI version** for the App Store, rather than wrapping the web app with Capacitor. The web app stays as the prototype and as the free Safari version.

## Headline feature: the reading tool (for reading One Piece in Japanese)
The goal is to help you read the page yourself, **never translating unless you ask**.

1. **Books.** Create a book (for example "One Piece, volume 1"). Each book keeps its pages, its words and its stats.
2. **Capture.** Photograph a speech bubble or a page and crop to the bubble. Text is recognized on the phone (Apple Vision supports Japanese).
3. **Colored sentence.** Split the sentence into words and color each word by mastery: black, red, yellow, green, blue. No translation is shown.
4. **Tap a word** to see its reading and meaning from the bundled dictionary. Conjugated forms map to the dictionary form (食べた → 食べる).
5. **Flashcards with context.** One tap adds the word. The card keeps the original sentence and the cropped bubble image, shown on the back of the card.
6. **Translate on request only.** A "Translate this sentence" button, using Apple's on-device Translation framework (Japanese → French or English, free).
7. **Book stats.** Unique words, the percentage you know (watch it climb volume after volume), and the words learned from each book.

Manga-specific problems to test on real pages:
- vertical text and hand-lettered sound effects (fallback: an open-source manga text-recognition model bundled as Core ML)
- furigana: separate them from the main text, then use them to confirm readings
- splitting into words (Japanese has no spaces): Apple's NaturalLanguage tokenizer plus the dictionary

Option before the native app: a web prototype in the current app that uses the personal Claude key to read the photo. The rest of the flow (coloring, lookup, flashcards, translation only on request) would work the same.

Pages stay on the device and are never uploaded or shared.

## Other features that would set the app apart
- **"Read the world" camera:** live camera view with kanji colored by mastery (menus, signs, screens)
- **"How much can I read?":** share any Japanese text into the app to see it colored, with a "you know 78%" score, and queue the unknown words
- **On-device AI (Apple Foundation Models, iOS 26, iPhone 15 Pro and later):** free memory stories in English or French, and example sentences that only use kanji you know plus one new one. The hand-written stories stay as the fallback.
- **Smart ordering by parts:** learn the components before the kanji built from them (木 before 休 and 林)
- **Handwriting practice:** draw with a finger or Apple Pencil, checked stroke by stroke against the KanjiVG stroke-order data
- **Best-in-class French:** French throughout, including example sentences
- **FSRS:** a better review scheduler (open-source, used by Anki)
- **Widgets:** the kanji map filling up, kanji of the day, today's count
- **Hands-free audio mode** (and CarPlay later)
- **Daily reminder notification**, real haptics, and the native Japanese voice
- **iCloud sync** of progress (stored in each user's own iCloud, so no cost)
- Kana decks (hiragana and katakana), decks by textbook lesson (Genki, Minna no Nihongo), written stories for the N3 kanji

## Before publishing publicly
- [ ] Pick a public name that doesn't start with "Anki" (AnkiMobile exists) and isn't from One Piece
- [ ] Add a data license file: dict.json, kanji.json and the stroke files are CC BY-SA (JMdict and KANJIDIC: 4.0, KanjiVG: 3.0). App code and design don't have to be open source.
- [ ] Settings → About: add a link to the EDRDG licence page (https://www.edrdg.org/edrdg/license.html)
- [ ] Monthly GitHub job that rebuilds the data from the latest JMdict and KANJIDIC release (required by the EDRDG licence)
- [ ] Remove "Use my Treasure Log key". Decide whether the Claude button stays (users must bring their own key) or is replaced by on-device AI.
- [ ] Don't present JLPT levels as official
- [ ] Privacy policy (simple: nothing leaves the device)
- [ ] App Store: Apple Developer account; build with Xcode 26 on the MacBook
- [ ] Moving from the web version: save a backup file in Safari, then restore it in the native app

## Licenses in use (checked November 2026)
| Data | License |
|---|---|
| KANJIDIC2, JMdict (EDRDG) | CC BY-SA 4.0: commercial use allowed, credit on a separate screen, keep data updated |
| Tatoeba example sentences | CC BY 2.0 FR |
| KanjiVG stroke order and parts | CC BY-SA 3.0 |
| kanji-data (JLPT levels from Jonathan Waller's lists) | MIT; no WaniKani fields are shipped |
| open-anki-jlpt-decks | MIT |
| Memory stories, French gap-fill, part names, icons, design, code | Written for this project |
| Voice | iOS system voices (nothing distributed) |
| Fonts | iOS system fonts; Klee One and Shippori Mincho (SIL OFL) |
