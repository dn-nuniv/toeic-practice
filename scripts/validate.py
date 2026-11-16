# -*- coding: utf-8 -*-
"""問題バンクの機械チェック。生成のたびに実行する。
  python3 scripts/validate.py
エラー（形式の誤り）は終了コード1。警告（品質の注意）は表示のみ。"""
import json, pathlib, sys, difflib, re
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
items = json.loads((ROOT / "data/items.json").read_text(encoding="utf-8"))
sets = json.loads((ROOT / "data/sets.json").read_text(encoding="utf-8"))
E, W = [], []
N_OPTS = {1: 4, 2: 3, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4}
REQ = ["id", "part", "type", "prompt", "options", "answer", "explanation_ja", "status"]

ids = Counter(i["id"] for i in items)
for k, n in ids.items():
    if n > 1: E.append(f"重複ID: {k}")
sid = {s["id"]: s for s in sets}
by_id = {i["id"]: i for i in items}

for it in items:
    t = it["id"]
    for f in REQ:
        if it.get(f) in (None, "", []): E.append(f"{t}: {f} が空")
    oids = [o["id"] for o in it["options"]]
    if len(oids) != N_OPTS[it["part"]]: E.append(f"{t}: 選択肢の数 {len(oids)}（Part{it['part']} は {N_OPTS[it['part']]}）")
    if len(set(oids)) != len(oids): E.append(f"{t}: 選択肢IDの重複")
    if it["answer"] not in oids: E.append(f"{t}: 正解ID {it['answer']} が選択肢にない")
    if len({o['text'].strip().lower() for o in it['options']}) != len(oids): E.append(f"{t}: 同じ文の選択肢がある")
    tro = it.get("translation_options_ja")
    if tro and len(tro) != len(oids): E.append(f"{t}: 選択肢の和訳の数が合わない")
    on = it.get("option_notes_ja")
    if on is not None:
        if len(on) != len(oids): E.append(f"{t}: 選択肢ごとのコメントの数が合わない")
        elif any(re.search(r"\([A-D]\)", x or "") for x in on): E.append(f"{t}: 選択肢ごとのコメントに (A)〜(D) の記号がある（表示順が変わるので中身で書く）")
        elif not all((x or "").strip() for x in on): E.append(f"{t}: 空の選択肢コメントがある")
    if it.get("set_id"):
        s = sid.get(it["set_id"])
        if not s: E.append(f"{t}: set_id {it['set_id']} がない")
        elif t not in s["question_ids"]: E.append(f"{t}: セット {s['id']} の question_ids に入っていない")
        elif s["part"] != it["part"]: E.append(f"{t}: セットとPartが違う")
    elif it["part"] in (1, 3, 4, 6, 7):
        E.append(f"{t}: Part{it['part']} なのに set_id がない")
    # 品質の警告：正解だけが極端に長い（AI作成の問題で起きやすい）
    if it["part"] not in (1, 2) and it.get("shuffle", True):
        L = {o["id"]: len(o["text"]) for o in it["options"]}
        others = [v for k, v in L.items() if k != it["answer"]]
        if others and L[it["answer"]] > 1.6 * max(others) and L[it["answer"]] > 25:
            W.append(f"{t}: 正解の選択肢だけが長い（{L[it['answer']]}字 / 他の最大 {max(others)}字）")

for s in sets:
    for q in s["question_ids"]:
        if q not in by_id: E.append(f"{s['id']}: 設問 {q} がない")
    if s["part"] in (3, 4) and not s["segments"]: E.append(f"{s['id']}: スクリプトがない")
    if s["part"] in (6, 7) and not s["passages"]: E.append(f"{s['id']}: 本文がない")
    if s["part"] == 1:
        if not s.get("image"): E.append(f"{s['id']}: 写真がない")
        elif not (ROOT / s["image"]).exists(): W.append(f"{s['id']}: 写真ファイル {s['image']} が見つからない")
    spk = {p["id"] for p in s["speakers"]}
    for g in s["segments"]:
        if g["speaker"] not in spk: E.append(f"{s['id']}: 話者 {g['speaker']} が speakers にない")
    if s["part"] == 6:
        text = "".join(p["text"] for p in s["passages"])
        blanks = re.findall(r"\[(\d)\]", text)
        if len(blanks) != len(s["question_ids"]): E.append(f"{s['id']}: 空欄の数 {len(blanks)} と設問数が違う")

# 似すぎた問題（重複生成の検出）
# Part 2・5 は設問文どうし、セットの問題（Part 3・4・6・7）は会話・本文どうしを比べる。
# Part 3・4・7 の設問は "What does the man say he will do?" のような決まった型なので、設問文では比べない。
def near(lst, label):
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            r = difflib.SequenceMatcher(None, lst[i][1], lst[j][1]).ratio()
            if r > 0.88: W.append(f"{label}: {lst[i][0]} / {lst[j][0]}（類似度 {r:.2f}）")


def body(s):
    return " ".join([g["text"] for g in s["segments"]] + [x.get("text", "") for x in s["passages"]]).lower()


for p in (2, 5):
    near([(it["id"], it["prompt"].lower()) for it in items if it["part"] == p], "似た問題")
for p in (3, 4, 6, 7):
    near([(s["id"], body(s)) for s in sets if s["part"] == p], "似たセット")

# 単語（data/vocab.json）
vpath = ROOT / "data/vocab.json"
vocab = json.loads(vpath.read_text(encoding="utf-8")) if vpath.exists() else []
vby = {w["id"]: w for w in vocab}
for w in vocab:
    t = w["id"]
    for f in ("word", "meaning_ja", "example", "example_ja", "cloze"):
        if not str(w.get(f, "")).strip(): E.append(f"{t}: {f} が空")
    n = len(re.findall(rf"(?<![A-Za-z]){re.escape(w['cloze'])}(?![A-Za-z])", w["example"]))
    if n == 0: E.append(f"{t}: 穴埋めの語 '{w['cloze']}' が例文にない")
    elif n > 1: W.append(f"{t}: 穴埋めの語 '{w['cloze']}' が例文に {n} 回ある（最初の1つを空欄にする）")
    if len(w["distractors"]) < 3: E.append(f"{t}: 同じ品詞のダミーが3つ取れない（{len(w['distractors'])}つ）")
    ms = [vby[c]["meaning_ja"] for c in w["choices"] if c in vby]
    if len(set(ms)) != len(ms): E.append(f"{t}: 4択に同じ意味が並ぶ")
    if len(w["cloze"]) < 3: W.append(f"{t}: 穴埋めの語が短すぎてヒントにならない")
    if any(x.lower() in (w["word"].lower(), w["cloze"].lower()) for x in w.get("also_ok", [])): W.append(f"{t}: 別解（also_ok）に見出し語・穴埋めの語と同じものがある")
    if re.search(r"https?://|www\.", w["example"]) and ".example" not in w["example"]: E.append(f"{t}: 例文の URL は .example ドメインに")
for k, n in Counter(w["word"].lower() for w in vocab).items():
    if n > 1: W.append(f"同じ見出し語が {n} 回: {k}")
for k, n in Counter((w["pos"], w["meaning_ja"]) for w in vocab).items():
    if n > 1: W.append(f"同じ品詞・同じ意味の単語が {n} 語: {k[1]}（4択で両方が正解に見える）")

# 厚い解説（選択肢ごとのコメント・TOEIC のポイント）がまだの問題
thin = [it["id"] for it in items if it["status"] != "retired" and not (it.get("option_notes_ja") and it.get("point_ja"))]
if thin: W.append(f"解説がまだ厚くなっていない問題 {len(thin)}問（選択肢ごとのコメント・TOEIC のポイント）: Part別 {dict(sorted(Counter(i.split('-')[0] for i in thin).items()))}")

# 位置固定の問題で正解の位置が偏っていないか
fixed = [it for it in items if not it.get("shuffle", True)]
pos = Counter([o["id"] for o in it["options"]].index(it["answer"]) for it in fixed)
print("Part別の問題数:", dict(sorted(Counter(i["part"] for i in items).items())))
if vocab: print("単語:", len(vocab), "語 / 品詞:", dict(Counter(w["pos"] for w in vocab)), "/ 状態:", dict(Counter(w["status"] for w in vocab)))
print("出題タイプ:", len(Counter(i["type"] for i in items)), "種類 / 状態:", dict(Counter(i["status"] for i in items)))
if fixed: print("位置固定の問題の正解位置:", {"ABCD"[k]: v for k, v in sorted(pos.items())})
for w in W: print("警告:", w)
for e in E: print("エラー:", e)
print(f"エラー {len(E)} 件 / 警告 {len(W)} 件")
sys.exit(1 if E else 0)
