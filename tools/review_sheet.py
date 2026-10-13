"""Draw side-by-side pairs of (card, closest existing print) with their art-match score, for tuning."""
import json, pathlib, sys, cv2, numpy as np
ROOT = pathlib.Path(__file__).resolve().parent.parent
checks = json.loads((ROOT / "data/art_checks.json").read_text())
cache = pathlib.Path(sys.argv[1]); out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
lo, hi = int(sys.argv[3]), int(sys.argv[4])
items = sorted([(v["best"], k, v["best_id"]) for k, v in checks.items() if v.get("best_id") and lo <= v["best"] <= hi])
def load(i):
    im = cv2.imread(str(cache / f"{i}.png"))
    return cv2.resize(im, (150, 210)) if im is not None else np.full((210, 150, 3), 128, np.uint8)
tiles = []
for s, a, b in items:
    t = np.hstack([load(a), np.full((210, 4, 3), 255, np.uint8), load(b)])
    t = np.vstack([np.full((30, t.shape[1], 3), 255, np.uint8), t])
    cv2.putText(t, f"{s}  {a}", (4, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 200), 1, cv2.LINE_AA)
    tiles.append(cv2.copyMakeBorder(t, 3, 3, 3, 3, cv2.BORDER_CONSTANT, value=(40, 40, 40)))
per = 24
for n in range(0, len(tiles), per):
    chunk = tiles[n:n + per]
    while len(chunk) % 4: chunk.append(np.full_like(tiles[0], 40))
    rows = [np.hstack(chunk[i:i + 4]) for i in range(0, len(chunk), 4)]
    cv2.imwrite(str(out / f"sheet_{lo}_{hi}_{n // per:02d}.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 70])
print(len(items), "pairs")
