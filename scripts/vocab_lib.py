# -*- coding: utf-8 -*-
"""単語データ（data/vocab/src/*.json）の読み込みと、build・validate・レビューで共通に使う処理。
書き方は data/vocab/README.md を参照。"""
import hashlib, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "vocab" / "src"
POS = {"noun", "verb", "adjective", "adverb", "phrase"}
LEVELS = ["A1", "A2", "B1", "B2", "C1"]
REQ = {"id", "word", "pos", "meaning_ja", "level", "example", "example_ja", "cloze"}
OPT = {"status", "source", "distractors", "also_ok", "also_ok_cloze", "note"}


def h(s):
    return hashlib.sha1(s.encode()).hexdigest()


def load(errors):
    """問題ファイルを読み、行（辞書）のリストを返す。誤りは errors に足す"""
    words = []
    for f in sorted(SRC.glob("*.json")):
        rel = f.relative_to(ROOT)
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{rel}: JSON の形が正しくない（{e.lineno}行目: {e.msg}）"); continue
        for k in sorted({"batch", "source", "words"} - doc.keys()): errors.append(f"{rel}: {k} がない")
        for k in sorted(doc.keys() - {"batch", "source", "note", "words"}): errors.append(f"{rel}: 知らない項目 {k}")
        for n, w in enumerate(doc.get("words", [])):
            where = f"{rel} > {w.get('id', f'単語{n + 1}') if isinstance(w, dict) else f'単語{n + 1}'}"
            if not isinstance(w, dict): errors.append(f"{where}: オブジェクトではない"); continue
            for k in sorted(REQ - w.keys()): errors.append(f"{where}: {k} がない")
            for k in sorted(w.keys() - REQ - OPT): errors.append(f"{where}: 知らない項目 {k}（書き間違い？）")
            if REQ - w.keys(): continue
            if not re.fullmatch(r"v-\d{4}", w["id"]): errors.append(f"{where}: ID が v-0000 の形でない")
            if w["pos"] not in POS: errors.append(f"{where}: pos は {sorted(POS)} のどれか")
            if w["level"] not in LEVELS: errors.append(f"{where}: level は {LEVELS} のどれか")
            if w.get("status", "draft") not in ("draft", "retired"): errors.append(f"{where}: status は draft か retired")
            words.append(dict(id=w["id"], word=w["word"], pos=w["pos"], meaning_ja=w["meaning_ja"], level=w["level"],
                              example=w["example"], example_ja=w["example_ja"], cloze=w["cloze"], also_ok=w.get("also_ok", []), also_ok_cloze=w.get("also_ok_cloze", []),
                              status=w.get("status", "draft"), source=w.get("source", doc.get("source", "")),
                              fixed_distractors=w.get("distractors")))
    return words


def forms(word):
    """問題文の中で、この単語とみなす語形（簡単な語形変化）"""
    w = word.lower()
    out = {w, w + "s", w + "es", w + "ed", w + "d", w + "ing", w + "er", w + "ly"}
    if w.endswith("e"): out |= {w[:-1] + "ing", w[:-1] + "ed"}
    if w.endswith("y"): out |= {w[:-1] + "ies", w[:-1] + "ied"}
    if re.search(r"[^aeiou][aeiou][bdgmnprt]$", w): out |= {w + w[-1] + "ed", w + w[-1] + "ing"}  # stop → stopped
    return out


def item_tokens(items, sets):
    """問題ごとに、本文・設問・選択肢に出てくる語の集合"""
    sets = {s["id"]: s for s in sets}
    out = {}
    for it in items:
        t = [it["prompt"]] + [o["text"] for o in it["options"]]
        s = sets.get(it.get("set_id"))
        if s:
            t += [g["text"] for g in s["segments"]] + [p.get("text", "") for p in s["passages"]]
            t += [" ".join(" ".join(r) for r in (p.get("table") or {}).get("rows", [])) for p in s["passages"]]
        text = " ".join(t).lower()
        out[it["id"]] = (set(re.findall(r"[a-z][a-z\-]*", text)), " " + " ".join(re.findall(r"[a-z][a-z\-']*", text)) + " ")
    return out


def appears(w, tok):
    """この語（熟語はひと続きの形）が問題に出てくるか。tok は item_tokens の値"""
    words, text = tok
    parts = w["word"].lower().split()
    if len(parts) == 1: return bool(forms(parts[0]) & words)
    head = "|".join(re.escape(f) for f in forms(parts[0]))  # 熟語は先頭の語だけ語形変化を見る（look → looking forward to）
    return re.search(rf" (?:{head}) {re.escape(' '.join(parts[1:]))} ", text) is not None


def pick_distractors(w, pool):
    """英→日の4択のダミー3つ：同じ品詞・近いレベルから決まった順で選ぶ（データに残してレビューできるようにする）"""
    if w.get("fixed_distractors"): return w["fixed_distractors"]
    lv = LEVELS.index(w["level"])
    cand = [x for x in pool if x["id"] != w["id"] and x["pos"] == w["pos"] and x["status"] != "retired"
            and x["meaning_ja"] != w["meaning_ja"]]
    cand.sort(key=lambda x: (abs(LEVELS.index(x["level"]) - lv) > 1, h(w["id"] + "|" + x["id"])))
    return [x["id"] for x in cand[:3]]


def choices(w):
    """4択の並び（レビュー用の書き出しで使う決まった順。アプリでは毎回シャッフルする）"""
    return sorted([w["id"]] + w["distractors"], key=lambda c: h(w["id"] + "#" + c))


def content_hash(w, meaning):
    """レビューがどの版の単語に対するものか（見出し語・意味・例文・穴埋め・4択の中身が変わると変わる）"""
    body = {k: w[k] for k in ("word", "pos", "meaning_ja", "example", "example_ja", "cloze")}
    body["choices"] = [meaning[c] for c in w["choices"]]
    return h(json.dumps(body, ensure_ascii=False, sort_keys=True))[:12]


def hint(s):
    """記述問題のヒント：各語の最初の文字＋残りの字数分の下線（熟語は look forward to → l___ f______ t_）"""
    return " ".join(t[0] + "".join(c if c in "-'" else "_" for c in t[1:]) for t in s.split(" "))
