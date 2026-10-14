"""Weekly PriceCharting prices for the cards in data/cards.json (personal use).

- Reads each Japanese set list from PriceCharting (JSON pages, a few seconds apart).
- Matches every Log Pose card to a PriceCharting product:
    regular print  -> the product with the same card number and no [tag]
    other prints   -> among products with the same card number, the one whose picture matches ours
- data/pc_map.json : card id -> PriceCharting product (id, name, link). No prices in it.
- data/prices.enc  : price history (ungraded, USD cents), ENCRYPTED with PRICE_PASSPHRASE,
                     so the public site does not republish PriceCharting's data.
- data/pc_report.json : match statistics (no prices).

Usage (in the GitHub Action):  PRICE_PASSPHRASE=... python tools/pc_prices.py --img-cache .pccache
"""
import argparse, base64, datetime, json, os, pathlib, re, sys, time
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UA = {"User-Agent": "log-pose-personal-collection/1.0 (weekly, low volume)"}
PC = "https://www.pricecharting.com"
PAGES = {
    "OP01": "romance-dawn", "OP02": "paramount-war", "OP03": "pillars-of-strength",
    "OP04": "kingdoms-of-intrigue", "OP05": "awakening-of-the-new-era", "OP06": "wings-of-the-captain",
    "OP07": "500-years-in-the-future", "OP08": "two-legends", "OP09": "emperors-in-the-new-world",
    "OP10": "royal-blood", "OP11": "fist-of-divine-speed", "OP12": "legacy-of-the-master",
    "OP13": "carrying-on-his-will", "OP14": "azure-sea's-seven", "OP15": "adventure-on-kami's-island",
    "OP16": "the-time-of-battle", "OP17": "world's-strongest-warriors",
    "EB01": "extra-booster-memorial-collection", "EB02": "extra-booster-anime-25th-collection",
    "EB03": "extra-booster-heroines-edition", "EB04": "extra-booster-egghead-crisis",
    "PRB01": "premium-booster", "PRB02": "premium-booster-2",
}
CODE_RE = re.compile(r"\b((?:OP|EB|PRB|ST|P)\d*-\d{3})\b", re.I)
TAG_RE = re.compile(r"\[([^\]]*)\]")
# tags that are never one of our prints (promos, anniversaries, serials, event prizes...)
SKIP = re.compile(r"anniversary|girls|promotion|flagship|serial|weekly|jump|box topper|film|wanted|ultra deck|"
                  r"pre-?release|championship|judge|winner|tournament|stamp|gift|celebration|store|event|"
                  r"standard battle|treasure cup|dash pack|starter|best selection|errata|sealed|bandai card fest|"
                  r"premium card collection|illustration box|double pack|demo", re.I)


def fetch_set(slug, delay):
    out, cursor = [], "0"
    for _ in range(12):
        url = f"{PC}/console/one-piece-japanese-{slug}?sort=&cursor={cursor}&format=json"
        r = requests.get(url, headers=UA, timeout=60)
        r.raise_for_status()
        d = r.json()
        prods = d.get("products") or []
        out += prods
        time.sleep(delay)
        nxt = d.get("cursor")
        if not prods or not nxt or nxt == cursor or len(prods) < 150:
            break
        cursor = nxt
    return out


def cents(s):
    s = (s or "").replace("$", "").replace(",", "").strip()
    try:
        return int(round(float(s) * 100)) if s else None
    except ValueError:
        return None


# ---------------- picture comparison ----------------
class Pics:
    def __init__(self, cache):
        import cv2, numpy as np
        self.cv2, self.np = cv2, np
        self.cache = pathlib.Path(cache); self.cache.mkdir(parents=True, exist_ok=True)
        self.orb = cv2.ORB_create(nfeatures=800, scaleFactor=1.15, nlevels=8)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.memo = {}

    def _prep(self, im):
        cv2, np = self.cv2, self.np
        g = cv2.cvtColor(cv2.resize(im, (300, 419)), cv2.COLOR_BGR2GRAY)
        mask = np.zeros_like(g); mask[40:190, 15:285] = 255         # artwork area above the text box
        kp, des = self.orb.detectAndCompute(g, mask)
        hsv = cv2.cvtColor(cv2.resize(im, (300, 419))[40:190, 15:285], cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [24, 16], [0, 180, 0, 256]); cv2.normalize(hist, hist)
        return kp, des, hist

    def ours(self, cid):
        k = "o:" + cid
        if k not in self.memo:
            p = ROOT / "img" / f"{cid}.webp"
            im = self.cv2.imread(str(p)) if p.exists() else None
            self.memo[k] = self._prep(im) if im is not None else None
        return self.memo[k]

    def theirs(self, prod):
        k = "t:" + prod["id"]
        if k not in self.memo:
            p = self.cache / f"{prod['id']}.jpg"
            if not p.exists():
                url = (prod.get("imageUri") or "").rsplit("/", 1)[0] + "/240.jpg"
                try:
                    r = requests.get(url, headers=UA, timeout=60)
                    if r.ok:
                        p.write_bytes(r.content)
                    time.sleep(0.3)
                except Exception:
                    pass
            im = self.cv2.imread(str(p)) if p.exists() else None
            self.memo[k] = self._prep(im) if im is not None else None
        return self.memo[k]

    def score(self, cid, prod):
        a, b = self.ours(cid), self.theirs(prod)
        if not a or not b or a[1] is None or b[1] is None:
            return 0.0
        cv2, np = self.cv2, self.np
        pairs = self.bf.knnMatch(a[1], b[1], k=2)
        good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.78 * n.distance]
        inl = 0
        if len(good) >= 8:
            src = np.float32([a[0][m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst = np.float32([b[0][m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            H, mk = cv2.findHomography(src, dst, cv2.RANSAC, 8.0)
            inl = int(mk.sum()) if mk is not None else 0
        col = float(cv2.compareHist(a[2], b[2], cv2.HISTCMP_CORREL))
        return inl + 20 * max(col, 0)            # shape matches dominate, colour breaks ties


def tag_of(name):
    m = TAG_RE.search(name)
    return m.group(1).strip() if m else ""


def match(cards, products, pics):
    by_code = {}
    for p in products:
        m = CODE_RE.search(p.get("productName", ""))
        if m:
            by_code.setdefault(m.group(1).upper(), []).append(p)
    mapping, report = {}, {"matched": 0, "unmatched": [], "low_confidence": []}
    taken = {}
    for c in cards:
        cid, code, series = c["id"], c["code"], c["set"][:2]
        cands = by_code.get(code, [])
        if c["kind"] == "regular" and "_" not in cid:
            base = [p for p in cands if not tag_of(p["productName"])]
            if base:
                mapping[cid] = base[0]; continue
            report["unmatched"].append(cid); continue
        alts = [p for p in cands if tag_of(p["productName"]) and not SKIP.search(tag_of(p["productName"]))]
        is_prb = c["set"].startswith("PRB")
        # PriceCharting marks premium-booster prints with "PRB01"/"PRB02" in the tag
        pref = [p for p in alts if (re.search(r"prb", tag_of(p["productName"]), re.I) is not None) == is_prb]
        pool = pref or alts
        if not pool:
            report["unmatched"].append(cid); continue
        scored = sorted(((pics.score(cid, p), p) for p in pool), key=lambda x: -x[0])
        best, p = scored[0]
        second = scored[1][0] if len(scored) > 1 else 0
        if best < 12:
            report["unmatched"].append(cid); continue
        if len(scored) > 1 and best - second < 5:
            report["low_confidence"].append(cid)
        # one PriceCharting product per card: keep the better-scoring card
        if p["id"] in taken and taken[p["id"]][1] >= best:
            report["unmatched"].append(cid); continue
        if p["id"] in taken:
            old = taken[p["id"]][0]; mapping.pop(old, None); report["unmatched"].append(old)
        taken[p["id"]] = (cid, best)
        mapping[cid] = p
    report["matched"] = len(mapping)
    return mapping, report


# ---------------- encryption (AES-GCM, key from passphrase via PBKDF2) ----------------
ITER = 200_000


def _key(passphrase, salt):
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(passphrase.encode())


def encrypt(obj, passphrase):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(_key(passphrase, salt)).encrypt(iv, json.dumps(obj, separators=(",", ":")).encode(), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"v": 1, "kdf": "PBKDF2-SHA256", "iter": ITER, "salt": b(salt), "iv": b(iv), "ct": b(ct)}


def decrypt(env, passphrase):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    d = lambda x: base64.b64decode(x)
    return json.loads(AESGCM(_key(passphrase, d(env["salt"]))).decrypt(d(env["iv"]), d(env["ct"]), None))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img-cache", default=".pccache")
    ap.add_argument("--delay", type=float, default=4.0)
    a = ap.parse_args()
    pw = os.environ.get("PRICE_PASSPHRASE", "")
    if not pw:
        sys.exit("PRICE_PASSPHRASE secret is not set - add it in the repo settings (Secrets and variables > Actions).")

    doc = json.loads((DATA / "cards.json").read_text(encoding="utf-8"))
    cards = [dict(c, set=s["code"]) for s in doc["sets"] for c in s["cards"]]

    products = []
    for code, slug in PAGES.items():
        try:
            got = fetch_set(slug, a.delay)
            for p in got: p["_page"] = code
            products += got
            print(f"{code}: {len(got)} products")
        except Exception as e:
            print(f"{code}: failed ({e})")

    mapping, report = match(cards, products, Pics(a.img_cache))

    # public: which product each card is (no prices)
    pc_map = {cid: {"pid": p["id"], "name": p["productName"],
                    "url": f"{PC}/game/{p['consoleUri']}/{p['productUri']}"} for cid, p in mapping.items()}
    (DATA / "pc_map.json").write_text(json.dumps(pc_map, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")

    # private: price history, encrypted
    today = datetime.date.today().isoformat()
    env_file = DATA / "prices.enc"
    hist = {"source": "PriceCharting (ungraded, USD cents)", "dates": [], "p": {}}
    if env_file.exists():
        try:
            hist = decrypt(json.loads(env_file.read_text()), pw)
        except Exception:
            print("Could not decrypt the existing price history (passphrase changed?) - starting a new one.")
    if hist["dates"] and hist["dates"][-1] == today:
        hist["dates"].pop()
        for v in hist["p"].values():
            if len(v) > len(hist["dates"]): v.pop()
    n = len(hist["dates"])
    hist["dates"].append(today)
    for cid, p in mapping.items():
        row = hist["p"].setdefault(cid, [])
        row += [None] * (n - len(row))
        row.append(cents(p.get("price1")))
    for cid, row in hist["p"].items():
        if len(row) < n + 1: row += [None] * (n + 1 - len(row))
    env_file.write_text(json.dumps(encrypt(hist, pw)))

    report.update({"date": today, "cards": len(cards), "products_seen": len(products)})
    (DATA / "pc_report.json").write_text(json.dumps(report, indent=1))
    print(f"matched {report['matched']}/{len(cards)}, unmatched {len(report['unmatched'])}, "
          f"low confidence {len(report['low_confidence'])}")


if __name__ == "__main__":
    main()
