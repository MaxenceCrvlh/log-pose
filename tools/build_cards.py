"""Build data/cards.json for Log Pose from the punk-records Japanese dataset.

Collection rules (Japanese cards, OP / EB / PRB only):
  OP & EB sets
    - regular prints: only foil rarities -> Leader, R, SR, SEC, SP, TR  (C and UC are not foil)
    - alternate prints (_p1, _p2 ...): Leader / SR / SEC / SP / TR / promo alt prints are always kept
      C / UC / R alternate prints are kept only if the ARTWORK is new; if the art matches the regular
      print it is a pirate / skull foil and is left out
  PRB sets
    - _r prints are reprints of existing art -> left out
    - other prints are kept only if the artwork does not exist on any print outside this PRB
  DON!! cards are never included.

Artwork comparison: ORB feature matching (robust to frame / crop / foil differences). Needs the
official images, so it runs in the GitHub Action (python tools/build_cards.py --check-art).
Results are cached in data/art_checks.json so later runs only look at new cards.

Usage:
  python tools/build_cards.py --punk path/to/punk-records/japanese [--check-art] [--img-cache .imgcache]
"""
import argparse, json, pathlib, re, sys, time, urllib.request, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FOIL = {"Leader", "Rare", "SuperRare", "SecretRare", "Special", "TreasureRare"}
ALWAYS_ALT = {"Leader", "SuperRare", "SecretRare", "Special", "TreasureRare", "Promo"}
NEEDS_ART_CHECK = {"Common", "Uncommon", "Rare"}
RAR_SHORT = {"Leader": "L", "Common": "C", "Uncommon": "UC", "Rare": "R", "SuperRare": "SR",
             "SecretRare": "SEC", "Special": "SP", "TreasureRare": "TR", "Promo": "P"}
SET_NAMES = {
    "OP01": "Romance Dawn", "OP02": "Paramount War", "OP03": "Pillars of Strength",
    "OP04": "Kingdoms of Intrigue", "OP05": "Awakening of the New Era", "OP06": "Wings of the Captain",
    "OP07": "500 Years in the Future", "OP08": "Two Legends", "OP09": "Emperors in the New World",
    "OP10": "Royal Blood", "OP11": "A Fist of Divine Speed", "OP12": "Legacy of the Master",
    "OP13": "Carrying On His Will", "OP14": "The Azure Sea's Seven", "OP15": "Adventure on Kami's Island",
    "OP16": "The Time of Battle", "OP17": "The World's Strongest Warriors",
    "EB01": "Memorial Collection", "EB02": "Anime 25th Collection", "EB03": "Heroines Edition",
    "EB04": "Extra Booster 4", "PRB01": "The Best", "PRB02": "The Best Vol. 2",
}
UA = {"User-Agent": "log-pose-builder/1.0 (personal collection checklist; github action)"}


def pack_code(pid):
    m = re.match(r"550(1|2|3)(\d\d)$", pid)
    if not m:
        return None
    return {"1": "OP", "2": "EB", "3": "PRB"}[m.group(1)] + m.group(2)


def base_code(cid):
    return cid.split("_")[0]


def suffix(cid):
    return cid[len(base_code(cid)):]          # "" | "_p1" | "_r2"


# ---------------- artwork comparison ----------------
class Art:
    def __init__(self, cache_dir, delay=0.25):
        import cv2  # noqa
        self.cv2 = cv2
        self.dir = pathlib.Path(cache_dir); self.dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.orb = cv2.ORB_create(nfeatures=1200, scaleFactor=1.15, nlevels=10)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.feat = {}

    def image(self, card):
        p = self.dir / (card["id"] + ".png")
        if not p.exists():
            req = urllib.request.Request(card["img_full_url"], headers=UA)
            for attempt in range(3):
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        p.write_bytes(r.read())
                    break
                except Exception as e:
                    if attempt == 2:
                        print("  download failed", card["id"], e); return None
                    time.sleep(2)
            time.sleep(self.delay)
        return self.cv2.imread(str(p))

    def features(self, card):
        if card["id"] in self.feat:
            return self.feat[card["id"]]
        im = self.image(card)
        if im is None:
            self.feat[card["id"]] = None; return None
        cv2, np = self.cv2, __import__("numpy")
        h, w = im.shape[:2]
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        g = cv2.resize(g, (600, 838))
        # artwork only: skip the cost/power corners, the "SAMPLE" band and everything below it
        # (text box, name bar, card number) - those are the same template on every card.
        mask = np.zeros_like(g)
        mask[int(838 * .10):int(838 * .44), int(600 * .05):int(600 * .95)] = 255
        kp, des = self.orb.detectAndCompute(g, mask)
        self.feat[card["id"]] = (kp, des)
        return kp, des

    def same_art_score(self, a, b):
        """Number of geometrically consistent ORB matches between two prints (0 = unrelated)."""
        cv2, np = self.cv2, __import__("numpy")
        fa, fb = self.features(a), self.features(b)
        if not fa or not fb or fa[1] is None or fb[1] is None:
            return None
        kp1, d1 = fa; kp2, d2 = fb
        pairs = self.bf.knnMatch(d1, d2, k=2)
        good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.75 * n.distance]
        if len(good) < 8:
            return len(good)
        src = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 6.0)
        return int(inl.sum()) if inl is not None else 0


METHOD = "orb-art-v2"
# inlier matches at/above this = same illustration (tuned with the review sheets, Oct 2026):
#   characters: same art in another crop / tint scores >= 44, different art <= 25
#   events: manga-style new art reuses manga panels and scores up to 64; same art >= 270
SAME_ART_MIN = {"Event": 70}
SAME_ART_DEFAULT = 40


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--punk", required=True, help="path to punk-records/japanese")
    ap.add_argument("--check-art", action="store_true")
    ap.add_argument("--img-cache", default=".imgcache")
    a = ap.parse_args()

    punk = pathlib.Path(a.punk)
    packs = {}
    for f in sorted((punk / "data").glob("*.json")):
        packs[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    by_code = {}                                         # base code -> [(pack_id, card)]
    for pid, cards in packs.items():
        for c in cards:
            by_code.setdefault(base_code(c["id"]), []).append((pid, c))

    checks_file = DATA / "art_checks.json"
    checks = json.loads(checks_file.read_text()) if checks_file.exists() else {}
    art = Art(a.img_cache) if a.check_art else None

    def art_is_new(card, compare_to):
        """True/False, or None when it could not be checked. compare_to: list of cards."""
        key = card["id"]
        cached = checks.get(key)
        if cached and cached.get("method") == METHOD and cached.get("against") == sorted(c["id"] for c in compare_to):
            best = cached["best"]
        elif art:
            best, best_id = 0, None
            for o in compare_to:
                s = art.same_art_score(card, o)
                if s is not None and s > best:
                    best, best_id = s, o["id"]
            checks[key] = {"best": best, "best_id": best_id, "method": METHOD, "against": sorted(c["id"] for c in compare_to)}
        else:
            return None
        if not compare_to:
            return True
        return best < SAME_ART_MIN.get(card.get("category"), SAME_ART_DEFAULT)

    sets = []
    unchecked = 0
    for pid in sorted(packs):
        code = pack_code(pid)
        if not code:
            continue
        series = re.match(r"[A-Z]+", code).group(0)
        out = []
        for c in packs[pid]:
            cat = (c.get("category") or "")
            if "don" in cat.lower():
                continue
            cid, rar, suf = c["id"], c.get("rarity") or "", suffix(c["id"])
            keep, check = False, None
            if series in ("OP", "EB"):
                if suf == "":
                    keep = rar in FOIL
                elif rar in ALWAYS_ALT:
                    keep = True
                elif rar in NEEDS_ART_CHECK:
                    regular = [o for p, o in by_code.get(base_code(cid), []) if suffix(o["id"]) == ""]
                    check = art_is_new(c, regular)
                    keep = check is not False
            else:  # PRB
                if suf.startswith("_r"):
                    keep = False
                else:
                    others = [o for p, o in by_code.get(base_code(cid), []) if p != pid]
                    check = art_is_new(c, others)
                    keep = check is not False
            if not keep:
                continue
            if check is None and (suf and (series == "PRB" or rar in NEEDS_ART_CHECK)):
                unchecked += 1
            kind = "regular" if suf == "" else ("sp" if rar == "Special" else "tr" if rar == "TreasureRare" else "alt")
            out.append({
                "id": cid, "code": base_code(cid), "name": c.get("name") or "", "r": RAR_SHORT.get(rar, rar),
                "cat": cat, "kind": kind, "img": c.get("img_full_url", "").split("?")[0],
                **({"unverified": True} if check is None and suf and (series == "PRB" or rar in NEEDS_ART_CHECK) else {}),
            })
        out.sort(key=lambda x: (x["code"], x["id"]))
        sets.append({"code": code, "series": series, "name": SET_NAMES.get(code, code), "pack": pid,
                     "cards": out})

    order = {"OP": 0, "EB": 1, "PRB": 2}
    sets.sort(key=lambda s: (order[s["series"]], s["code"]))
    DATA.mkdir(exist_ok=True)
    doc = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"), "source": "punk-records (official JP card list)",
           "art_checked": bool(art) or unchecked == 0, "sets": sets}
    (DATA / "cards.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if art or checks:
        checks_file.write_text(json.dumps(checks, indent=0, sort_keys=True), encoding="utf-8")
    tot = sum(len(s["cards"]) for s in sets)
    print(f"{len(sets)} sets, {tot} cards, {unchecked} not art-checked")
    for s in sets:
        print(f"  {s['code']:6s} {len(s['cards']):4d}")


if __name__ == "__main__":
    main()
