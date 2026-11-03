#!/usr/bin/env python3
"""Build Poneglyph's data files.

Inputs (downloaded into a folder passed as the first argument):
  kanji.json                      github.com/davidluzgouveia/kanji-data (from KANJIDIC2)
  n5.csv .. n1.csv                github.com/jamsinclair/open-anki-jlpt-decks (src/)
  jmdict-examples-eng-*.json      github.com/scriptin/jmdict-simplified releases

Outputs (into data/):
  kanji.json   every kanji with a JLPT level or a school grade
  dict.json    common JMdict words + every JLPT word, with one or two Tatoeba examples
"""
import csv, glob, json, os, re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "src"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
os.makedirs(OUT, exist_ok=True)

# ---------- kanji ----------
PROPER = {"japan", "japanese", "china", "chinese", "korea", "korean", "buddha", "buddhist", "buddhism", "shinto", "confucius",
          "confucian", "kyushu", "osaka", "kyoto", "tokyo", "edo", "india", "america", "england", "english", "europe", "france", "french", "germany", "german", "holland", "dutch", "spain", "russia", "asia", "i", "ii"}
def fix_case(m):
    # KANJIDIC via kanji-data comes in Title Case ("Counter For Days"): make it plain lower case, keeping names
    out = []
    for w in m.split(" "):
        core = re.sub(r"[^A-Za-z]", "", w)
        if core.lower() in PROPER: out.append(w[:1].upper() + w[1:].lower() if core.lower() != "i" else w)
        elif len(core) > 1 and core.isupper(): out.append(w)
        else: out.append(w.lower())
    return " ".join(out)

raw = json.load(open(os.path.join(SRC, "kanji.json"), encoding="utf-8"))
kanji = []
for ch, d in raw.items():
    # Jōyō kanji (school grades 1-6, 8) plus anything on a JLPT list; name-only kanji left out
    if not d.get("jlpt_new") and not (d.get("grade") or 99) <= 8:
        continue
    means = [m for m in d.get("meanings") or [] if "radical" not in m.lower()] or d.get("meanings") or []
    kanji.append({
        "c": ch,
        "s": d.get("strokes") or 0,
        "g": d.get("grade") or 0,
        "f": d.get("freq") or 0,
        "j": d.get("jlpt_new") or 0,
        "m": [fix_case(m) for m in means[:6]],
        "on": d.get("readings_on") or [],
        "kun": d.get("readings_kun") or [],
    })
# order: JLPT N5 first ... N1, then non-JLPT; inside, by frequency (unranked last), then strokes
kanji.sort(key=lambda k: (-(k["j"]) if k["j"] else 0, k["f"] or 9999, k["s"]))
kanji_set = {k["c"] for k in kanji}

# ---------- JLPT vocabulary ----------
jlpt = {}  # (expression, reading) -> (level, csv meaning)
for lvl in (5, 4, 3, 2, 1):
    with open(os.path.join(SRC, f"n{lvl}.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            e, r = row["expression"].strip(), row["reading"].strip()
            if not e:
                continue
            key = (e, r or e)
            if key not in jlpt:  # easiest level wins
                jlpt[key] = (lvl, row["meaning"].strip())

# ---------- dictionary ----------
path = sorted(glob.glob(os.path.join(SRC, "jmdict-examples-eng-*.json")))[-1]
jm = json.load(open(path, encoding="utf-8"))
by_form = {}
for w in jm["words"]:
    for k in w["kanji"]:
        by_form.setdefault(k["text"], []).append(w)
    for k in w["kana"]:
        by_form.setdefault(k["text"], []).append(w)

def is_common(w):
    return any(x.get("common") for x in w["kanji"]) or any(x.get("common") for x in w["kana"])

# match JLPT entries to JMdict ids
jlpt_by_id = {}
unmatched = []
for (e, r), (lvl, mean) in jlpt.items():
    cands = by_form.get(e, [])
    best = None
    for w in cands:
        kanas = [k["text"] for k in w["kana"]]
        if r in kanas or e in kanas:
            best = w if best is None or (is_common(w) and not is_common(best)) else best
    if best is None and cands:
        best = next((w for w in cands if is_common(w)), cands[0])
    if best is None:
        unmatched.append((e, r, lvl, mean))
        continue
    prev = jlpt_by_id.get(best["id"])
    if prev is None or lvl > prev[0]:
        jlpt_by_id[best["id"]] = (lvl, e, r)

POS_SHORT = {}
for tag, desc in jm["tags"].items():
    POS_SHORT[tag] = desc

def clean_pos(tags):
    out = []
    for t in tags:
        d = POS_SHORT.get(t, t)
        d = re.sub(r"\s*\(.*?\)", "", d)
        d = d.replace("Godan verb with", "godan verb,").replace(" ending", "")
        out.append(d)
    return "; ".join(dict.fromkeys(out))

entries = []
for w in jm["words"]:
    jl = jlpt_by_id.get(w["id"])
    if not is_common(w) and not jl:
        continue
    kf = [k["text"] for k in sorted(w["kanji"], key=lambda k: not k.get("common")) if "iK" not in k.get("tags", []) and "sK" not in k.get("tags", [])]
    rf = [k["text"] for k in sorted(w["kana"], key=lambda k: not k.get("common")) if "sk" not in k.get("tags", [])]
    if jl:  # put the JLPT spelling first
        e, r = jl[1], jl[2]
        if e in kf: kf.remove(e); kf.insert(0, e)
        if r in rf: rf.remove(r); rf.insert(0, r)
    # usually-kana words: show kana as the headword
    uk = bool(w["sense"]) and "uk" in (w["sense"][0].get("misc") or [])
    senses, examples = [], []
    BAD = ("vulgar", "euphemistic", "derogatory", "sensitive")
    for si, s in enumerate(w["sense"][:6]):
        gl = [g["text"] for g in s["gloss"] if g["lang"] == "eng"][:5]
        if not gl:
            continue
        misc = [POS_SHORT.get(m, m) for m in (s.get("misc") or []) if m not in ("uk",)]
        senses.append([clean_pos(s.get("partOfSpeech") or []), "; ".join(gl), ", ".join(misc[:2])])
        if si > 1 or any(b in m for m in misc for b in BAD):
            continue
        for ex in s.get("examples") or []:
            if len(examples) >= 2:
                break
            jp = next((x["text"] for x in ex["sentences"] if x["lang"] == "jpn"), None)
            en = next((x["text"] for x in ex["sentences"] if x["lang"] == "eng"), None)
            if jp and en and len(jp) <= 60:
                examples.append([jp, en])
    if not senses:
        continue
    item = {"i": w["id"], "k": kf[:3], "r": rf[:3], "s": senses}
    if jl: item["j"] = jl[0]; item["h"] = jl[1]
    if is_common(w): item["c"] = 1
    if uk: item["u"] = 1
    if examples: item["e"] = examples
    entries.append(item)

# JLPT words missing from JMdict: keep with the list's own meaning
for i, (e, r, lvl, mean) in enumerate(unmatched):
    entries.append({"i": f"x{i}", "k": [e] if e != r else [], "r": [r], "s": [["", mean, ""]], "j": lvl, "h": e})

# order: JLPT words first (N5..N1), then by headword
entries.sort(key=lambda x: (-(x.get("j") or 0), 0 if x.get("c") else 1))

with open(os.path.join(OUT, "kanji.json"), "w", encoding="utf-8") as f:
    json.dump(kanji, f, ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(OUT, "dict.json"), "w", encoding="utf-8") as f:
    json.dump({"date": jm.get("dictDate"), "words": entries}, f, ensure_ascii=False, separators=(",", ":"))

print("kanji", len(kanji), "by JLPT", {l: sum(1 for k in kanji if k["j"] == l) for l in (5, 4, 3, 2, 1, 0)})
print("dict words", len(entries), "JLPT", sum(1 for e in entries if e.get("j")), "unmatched", len(unmatched))
print("with examples", sum(1 for e in entries if e.get("e")))

# ---------- stroke order (KanjiVG) ----------
# optional second argument: a KanjiVG checkout. Writes data/strokes/<hex>.json = list of path "d" strings in stroke order.
if len(sys.argv) > 2:
    kvg = os.path.join(sys.argv[2], "kanji")
    sdir = os.path.join(OUT, "strokes")
    os.makedirs(sdir, exist_ok=True)
    n = 0
    for k in kanji:
        hx = format(ord(k["c"]), "05x")
        p = os.path.join(kvg, hx + ".svg")
        if not os.path.exists(p):
            continue
        svg = open(p, encoding="utf-8").read()
        paths = re.findall(r'<path id="kvg:[0-9a-f]+-s(\d+)"[^>]*\sd="([^"]+)"', svg)
        paths = [d for _, d in sorted(paths, key=lambda x: int(x[0]))]
        with open(os.path.join(sdir, hx + ".json"), "w") as f:
            json.dump(paths, f, separators=(",", ":"))
        n += 1
    print("stroke files", n)
