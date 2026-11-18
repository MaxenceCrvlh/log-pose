"""Where a promo card came from, worked out from the official list's 入手情報 (how to get it).

classify(text) -> (group code, English label, date)
  group code  one of GROUPS below
  label       short English description, e.g. "Weekly Shonen Jump No.33 · bundled with the issue"
  date        "YYYY-MM-DD" (magazine on-sale date), "YYYY-MM" or "YYYY" when the text says, else ""

Run directly to print how every source in data/src is classified:  python tools/promo_sources.py
"""
import re, unicodedata

# code, chip label, name, what it is
GROUPS = [
    ("JUMP", "Shonen Jump", "Weekly Shonen Jump", "Cards bundled with an issue, or sent to everyone who applied through an issue (mail-in)."),
    ("VJUMP", "V Jump", "V Jump", "Cards bundled with an issue of V Jump, or mail-in offers from it."),
    ("SAIKYO", "Saikyo Jump", "Saikyo Jump", "Cards bundled with an issue of Saikyo Jump, or mail-in offers from it."),
    ("MAG", "Books & mags", "Other magazines and books", "Jump GIGA, ONE PIECE magazine, the official complete guides and other books."),
    ("PACK", "Promo packs", "Promotion packs", "Packs handed out in stores and at events (Promotion Pack, Promotion Pack EX, campaign packs)."),
    ("CSET", "Promo sets", "Promotion card sets", "The yearly Promotion Card Set and its campaigns."),
    ("SBP", "Battle packs", "Standard Battle packs", "Packs given for taking part in Standard Battle events at stores."),
    ("TIE", "Tie-ups", "Tie-ups and campaigns", "7-Eleven, MOS Burger, Ichiban Kuji, serial-number campaigns, games and other collaborations."),
    ("EVENT", "Events", "Events and meetups", "Store meetups (交流会), Bandai Card Games Fest, ONE PIECE DAY and other visitor gifts."),
    ("FILM", "FILM RED", "ONE PIECE FILM RED", "Cinema giveaways for the film ONE PIECE FILM RED."),
    ("PRIZE", "Tournaments", "Tournament prizes", "Flagship Battle, Standard Battle, Championship and other tournament prizes."),
    ("PCC", "Premium coll.", "Premium Card Collections", "The Premium Card Collection boxes."),
    ("SETS", "Sets & mats", "Special sets and playmats", "Anniversary sets, Championship sets, storage box sets and playmats with a card."),
    ("OTHER", "Other", "Other promos", "Promos that fit none of the groups above."),
]
GROUP_CODES = [g[0] for g in GROUPS]

RULES = [  # first match wins
    ("MAG", r"ONE PIECE magazine|ワンピース・マガジン"),
    ("JUMP", r"週刊少年ジャンプ"),
    ("VJUMP", r"Vジャンプ"),
    ("SAIKYO", r"最強ジャンプ"),
    ("FILM", r"FILM RED.*入場者"),
    ("PCC", r"プレミアムカードコレクション"),
    ("CSET", r"プロモーションカードセット"),
    ("SBP", r"スタンダードバトルパック"),
    ("PACK", r"プロモーションパック|キャンペーンパック"),
    ("EVENT", r"交流会|来場|ONE PIECE DAY"),
    ("PRIZE", r"記念品|8パックバトル|チャンピオンシップ\d|チャンピオンシップ25"),
    ("MAG", r"ジャンプGIGA|勉タメジャンプ|ワンピース・マガジン|ONE PIECE magazine|COMPLETE GUIDE|ONE PIECE学園|付録"),
    ("SETS", r"ANNIVERSARY SET|チャンピオンシップセット|ストレージボックスセット|プレイマット"),
    ("TIE", r"タイアップ|一番くじ|キャンペーン|SOUND LOADER|ODYSSEY|MONSTERS|BASE SHOP|特典"),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Japanese -> English, longest first; whatever is left untranslated stays as it is
WORDS = [
    ("応募者全員大サービス", "mail-in offer"), ("応募者全員サービス", "mail-in offer"), ("付録", "bundled with the issue"),
    ("週刊少年ジャンプとONE PIECE", "Weekly Shonen Jump and ONE PIECE"), ("週刊少年ジャンプ", "Weekly Shonen Jump"),
    ("Vジャンプ", "V Jump"), ("ジャンプGIGA", "Jump GIGA"), ("最強ジャンプ", "Saikyo Jump"), ("勉タメジャンプ", "Bentame Jump"),
    ("ワンピース・マガジン", "ONE PIECE magazine"), ("別冊", "special issue"), ("特集", "feature"),
    ("ONE PIECE学園", "ONE PIECE Academy"), ("限定特典カード", "limited bonus card"), ("特典カード", "bonus card"),
    ("始めようキャンペーン", "Starter campaign"), ("トレジャーキャンペーンパック", "Treasure campaign pack"),
    ("3周年!ワンピースカード", "3rd anniversary "), ("ONE PIECEカードゲーム", ""), ("ONE PIECE カードゲーム", ""),
    ("プロモーションカードセット", "Promotion Card Set"), ("ゲットキャンペーン", "campaign"),
    ("プロモーションパック", "Promotion Pack"), ("スタンダードバトルパック", "Standard Battle Pack"),
    ("セブンイレブンタイアップキャンペーン", "7-Eleven tie-up campaign"), ("モスバーガータイアップキャンペーン", "MOS Burger tie-up campaign"),
    ("オリジナルカード", "card"), ("一番くじ", "Ichiban Kuji"), ("購入者特典", "purchase bonus"),
    ("シリアルナンバー入り", "Serial-numbered "), ("エース・サボ・ルフィ", "Ace, Sabo, Luffy"), ("ルフィ", "Luffy"), ("ナミ", "Nami"), ("ネフェルタリ・ビビ", "Nefertari Vivi"),
    ("デラックスエディション", "Deluxe Edition"), ("セットBOX特典", "set box bonus"), ("リミテッドカードコレクション", "Limited Card Collection"),
    ("プレミアムカードコレクション", "Premium Card Collection"), ("ベストセレクション", "Best Selection"),
    ("25周年エディション", "25th Anniversary Edition"), ("麦わらの一味", "Straw Hat Crew"), ("バロックワークス", "Baroque Works"),
    ("ウタ", "Uta"), ("メラメラの実争奪戦", "Mera Mera no Mi tournament"), ("Edition", "Edition"),
    ("オフィシャルプレイマット", "Official Playmat"), ("リミテッドエディション", "Limited Edition"), ("&カードセット", " & card set"),
    ("ストレージボックスセット", "storage box set"), ("プレミアムブースター", "Premium Booster"),
    ("チャンピオンシップセット", "Championship Set"), ("旧四皇", "former Four Emperors"), ("エース・サボ・ルフィ", "Ace, Sabo, Luffy"),
    ("入場者プレゼント", "cinema giveaway"), ("第2弾", "2nd wave"), ("チュートリアルデッキ", "tutorial deck"),
    ("フィナーレセット", "finale set"), ("アンコールパック", "encore pack"),
    ("小学生以下限定含む", "incl. under-12 sessions"), ("交流会", "Store meetup"), ("開催記念品", "participation gift"),
    ("来場記念品", "visitor gift"), ("来場者特典", "visitor gift"), ("来場", "visitor"),
    ("フラッグシップバトル", "Flagship Battle"), ("エクストラグランドバトル", "Extra Grand Battle"), ("スタンダードバトル", "Standard Battle"),
    ("8パックバトル", "8-Pack Battle"), ("チャンピオンシップ", "Championship"),
    ("1次予選", "1st qualifier"), ("2次予選", "2nd qualifier"), ("予選", "qualifier"), ("エリア決勝大会", "area finals"),
    ("エリア大会", "area event"), ("決勝トーナメント", "final tournament"), ("決勝大会", "finals"), ("権利獲得記念品", "qualifier prize"),
    ("上位記念品", "top finishers prize"), ("優勝記念品", "winner prize"), ("記念品", "prize"), ("上位", "top finishers"),
    ("優勝", "winner"), ("合併特大号", " double issue"), ("特大号", " issue"), ("号", ""),
]


def norm(t):
    t = unicodedata.normalize("NFKC", t or "")
    return re.sub(r"[​‐-―−]", lambda m: "" if m.group(0) == "​" else "-", t).strip()


def date_of(t):
    m = re.search(r"\((\d{4})年(\d{1,2})月(\d{1,2})日売\)", t)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(20\d\d)年(\d{1,2})月", t) or re.search(r"(20\d\d) ?(\d{1,2})月", t)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    m = re.search(r"(?<![\d.])(20\d\d)(?![\d])", t)
    return m.group(1) if m else ""


def nice_date(d):
    if not d:
        return ""
    p = d.split("-")
    if len(p) == 3:
        return f"{int(p[2])} {MONTHS[int(p[1]) - 1]} {p[0]}"
    if len(p) == 2:
        return f"{MONTHS[int(p[1]) - 1]} {p[0]}"
    return p[0]


def english(t, group):
    s = re.sub(r"\(\d{4}年\d{1,2}月\d{1,2}日売\)", "", t)          # the date is shown on its own
    s = re.sub(r"[『』「」]", "", s)
    s = re.sub(r"[〝〟]", " ", s)
    s = re.sub(r"(\d+)巻", r"vol.\1", s)
    # "2025年7月" / "2026 4月" / "9月" -> "Jul 2025" / "Apr 2026" / "Sep"
    s = re.sub(r"(20\d\d)年(\d{1,2})月~(\d{1,2})月", lambda m: f"{MONTHS[int(m.group(2))-1]}-{MONTHS[int(m.group(3))-1]} {m.group(1)}", s)
    s = re.sub(r"(20\d\d)年(\d{1,2})月", lambda m: f"{MONTHS[int(m.group(2))-1]} {m.group(1)}", s)
    s = re.sub(r"(20\d\d) ?(\d{1,2})月", lambda m: f"{MONTHS[int(m.group(2))-1]} {m.group(1)}", s)
    if group in ("VJUMP", "SAIKYO"):                                # "10月特大号" is the issue's cover month
        s = re.sub(r"(\d{1,2})月(?:特大)?号", lambda m: f" {MONTHS[int(m.group(1))-1]} issue ", s)
    s = re.sub(r"(\d{1,2})月", lambda m: MONTHS[int(m.group(1)) - 1], s)
    if group == "JUMP":
        s = re.sub(r"(\d+)・(\d+)合併特大号", r" No.\1-\2 double issue", s)
        s = re.sub(r"(\d+)号", r" No.\1", s)
    s = re.sub(r"ベスト(\d+)記念品", r" top \1 prize ", s)
    s = re.sub(r"ベスト(\d+)", r" top \1 ", s)
    s = re.sub(r"(\d+)年", r"\1", s)
    for ja, en in WORDS:
        s = s.replace(ja, f" {en} " if en else " ")
    s = s.replace("(", " (").replace(")", ") ")
    s = re.sub(r"\(\s*", "(", s)
    s = re.sub(r"\s*\)", ")", s)
    s = re.sub(r"(?<![A-Za-z0-9])-|-(?![A-Za-z0-9])", " ", s)    # keep 25-26, Sep-Nov; drop "- vol.6 -"
    s = re.sub(r"(\d)(Season)", r"\1 \2", s)
    s = re.sub(r"\s+", " ", s).strip(" ·")
    s = re.sub(r"\s+(bundled with the issue|mail-in offer|winner prize|top \d+ prize|top finishers prize|qualifier prize|"
               r"participation gift|visitor gift|limited bonus card|bonus card|purchase bonus|set box bonus|cinema giveaway)", r" · \1", s)
    return s


def classify(text):
    t = norm(text)
    group = next((g for g, rx in RULES if re.search(rx, t)), "OTHER")
    return group, english(t, group), date_of(t)


if __name__ == "__main__":
    import collections, json, pathlib
    src = pathlib.Path(__file__).resolve().parent.parent / "data" / "src"
    seen = collections.Counter()
    for pid in ("550901", "550801"):
        f = src / f"{pid}.json"
        if f.exists():
            for c in json.loads(f.read_text(encoding="utf-8")):
                seen[c.get("info") or ""] += 1
    by = collections.defaultdict(list)
    for t, n in seen.items():
        g, en, d = classify(t)
        by[g].append((d, n, en, t))
    for g in GROUP_CODES:
        if by[g]:
            print(f"\n== {g} ({sum(x[1] for x in by[g])} cards, {len(by[g])} releases)")
            for d, n, en, t in sorted(by[g], reverse=True):
                print(f"  {d:10} {n:3}  {en}   ← {t}")
