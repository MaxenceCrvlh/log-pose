# Log Pose

A checklist app for a **Japanese One Piece card collection**: the foil cards of every OP, EB and PRB set.

**Your collection is not in this repository.** Everything you tick is saved only on your own device (in the browser's storage). This repository only holds the empty app and the public card list.

## What counts
- **OP and EB sets:** Leaders, R, SR, SEC, SP and TR, plus every alternate art. C and UC are left out (not foil), and so are pirate / skull foils (C, UC or R reprints that only add foil, detected by comparing the artwork).
- **PRB sets:** only new illustrations. Reprints of existing art and DON!! cards are left out.
- **DON!! cards** (OP and EB sets only) come from PriceCharting's set lists, since the official card list doesn't include them.
- If a card slips through that you don't collect, open it (press and hold) and tick **Not collecting**.

## Install on iPhone
1. Open the site in **Safari**.
2. Tap **Share**, then **Add to Home Screen**.
3. Open Log Pose from its icon. It runs full-screen and works offline.

## Using it
- Tap a card to mark it owned (tap again to remove; **Undo** appears for a few seconds).
- Press and hold a card for details: number of copies, condition tags (damage, centering, whitening…), a comment, or **Not collecting**.
- The **Notes** tab lists every card with a tag or comment, filterable by tag.
- **Stats → Download all pictures** saves every card picture for offline use (do it once on Wi-Fi).

## Backups
Your collection lives only on your phone. Go to **Stats → Save backup file** and choose **Save to Files → iCloud Drive** now and then. On a new phone, install the app and use **Restore from file**.

## Card list
`data/cards.json` is built by `tools/build_cards.py` from [punk-records](https://github.com/buhbbl/punk-records), which is generated from the official Japanese card list. A GitHub Action rebuilds it every Monday, so new sets appear on their own. Card pictures load from the official site, onepiece-cardgame.com.

Card images and names ©Eiichiro Oda/Shueisha, Toei Animation, Bandai. This is a personal, non-commercial checklist.

## Prices (personal use)
- **PriceCharting:** a weekly GitHub job (`tools/pc_prices.py`) reads the Japanese set lists, matches each card (by number, and by picture for alternate prints) and saves ungraded prices **encrypted** in `data/prices.enc`, so this public site doesn't republish PriceCharting's data. Needs the repo secret `PRICE_PASSPHRASE`; enter the same passphrase once in **Stats → Value** to unlock. Card ↔ product matches are in `data/pc_map.json`, match statistics in `data/pc_report.json`.
- **Yuyu-tei:** enter prices yourself from a card's page (press and hold → Prices). Yuyu-tei doesn't allow automated access, so there's no automatic fetch.
