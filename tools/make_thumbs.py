"""Download every card in data/cards.json once and store a phone-sized WebP in img/.
The official site forbids showing its images on other sites (Cross-Origin-Resource-Policy),
so the app shows these copies instead. Only missing thumbnails are downloaded."""
import io, json, pathlib, sys, time, urllib.request
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "img"; OUT.mkdir(exist_ok=True)
cache = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
UA = {"User-Agent": "log-pose-builder/1.0 (personal collection checklist; github action)"}
cards = [c for s in json.loads((ROOT / "data/cards.json").read_text())["sets"] for c in s["cards"]]
new = fail = 0
for c in cards:
    dst = OUT / f"{c['id']}.webp"
    if dst.exists():
        continue
    src = cache / f"{c['id']}.png" if cache else None
    try:
        if src and src.exists():
            data = src.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(c["img"], headers=UA), timeout=60) as r:
                data = r.read()
            time.sleep(0.25)
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im = im.resize((360, round(360 * im.height / im.width)), Image.LANCZOS)
        im.save(dst, "WEBP", quality=72, method=6)
        new += 1
    except Exception as e:
        fail += 1; print("failed", c["id"], e)
print(f"{new} new thumbnails, {fail} failed, {len(cards)} cards")
