# Log Pose

A checklist app for a **Japanese One Piece card collection**: the foil cards of every OP, EB and PRB set, plus every promo card.

**Your collection is not in this repository.** Everything you tick is saved only on your own device (in the browser's storage). This repository only holds the empty app and the public card list.

## What counts
- **OP and EB sets:** Leaders, R, SR, SEC, SP and TR, plus every alternate art. C and UC are left out (not foil), and so are pirate / skull foils (C, UC or R reprints that only add foil, detected by comparing the artwork).
- **PRB sets:** only new illustrations. Reprints of existing art and DON!! cards are left out.
- **Promo tab:** every print is listed, foil or not, in three groups: **P-cards** (P-001 and so on), **Promo prints** (promotion versions of set cards) and **Limited** (cards that only come in limited products such as premium collections and gift sets). Use the *OP cards / ST cards / …* buttons to narrow a group down.
- **DON!! cards** (OP and EB sets only) come from PriceCharting's set lists, since the official card list doesn't include them.
- If a card slips through that you don't collect, open it (press and hold) and tick **Not collecting**.

## Install on iPhone
1. Open the site in **Safari**.
2. Tap **Share**, then **Add to Home Screen**.
3. Open Log Pose from its icon. It runs full-screen and works offline.

## Using it
- Tap a card to mark it owned (tap again to remove; **Undo** appears for a few seconds).
- Press and hold a card for details: number of copies, condition tags (damage, centering, whitening…), a comment, or **Not collecting**.
- **🛒 Shop** (next to All / Missing / Owned) shows what you are missing; there, tapping a card looks for it at your shops instead of ticking it (see *Buying on Buyee*).
- The **Notes** tab lists every card with a tag or comment, filterable by tag.
- **Stats → Download all pictures** saves every card picture for offline use (do it once on Wi-Fi).

## Backups
Your collection lives only on your phone. Go to **Stats → Save backup file** and choose **Save to Files → iCloud Drive** now and then. On a new phone, install the app and use **Restore from file**.

## Card list
Every Monday a GitHub Action reads the official Japanese card list (`tools/fetch_official.py`, saved in `data/src/`) and rebuilds `data/cards.json` (`tools/build_cards.py`), so a new set appears the week Bandai publishes it. If the official site can't be read one week, the previous copy is kept. Card pictures are phone-sized copies made from the official site, onepiece-cardgame.com.

A new set shows its Japanese title until an English name is added to `SET_NAMES` in `tools/build_cards.py`.

Card images and names ©Eiichiro Oda/Shueisha, Toei Animation, Bandai. This is a personal, non-commercial checklist.

## Prices (personal use)
- **PriceCharting:** a weekly GitHub job (`tools/pc_prices.py`) reads the Japanese set lists, matches each card (by number, and by picture for alternate prints) and saves ungraded prices **encrypted** in `data/prices.enc`, so this public site doesn't republish PriceCharting's data. Needs the repo secret `PRICE_PASSPHRASE`; enter the same passphrase once in **Stats → Value** to unlock. Card ↔ product matches are in `data/pc_map.json`, match statistics in `data/pc_report.json`.
- **Yuyu-tei:** enter prices yourself from a card's page (press and hold → Prices). Yuyu-tei doesn't allow automated access, so there's no automatic fetch.

## Buying on Buyee
Log Pose never orders anything and never touches your Buyee cart. It finds the listing and opens it on Buyee; you press **Add to cart** there.

1. **Stats → Buyee shopping → My Rakuten shops:** paste one link per shop (a shop or item link from Buyee or Rakuten works, or the shop's code).
2. **Rakuten key (free, once):** register an app at [webservice.rakuten.co.jp](https://webservice.rakuten.co.jp/) and copy its *Application ID* and *Access key* into the same panel, then **Save and test**. The key stays on your phone and is not written to backups.
3. In any set tap **🛒 Shop**, then a missing card. You get the in-stock listings for that card number at your shops, cheapest first; tap one to open it on Buyee.
4. Tick **It's in my Buyee cart** to put a 🛒 on the card until you mark it owned.

Without a key the sheet still gives one-tap links to the Buyee search for that card and to each of your shops on Buyee. Prices shown are the shops' own, before Buyee's fees.

