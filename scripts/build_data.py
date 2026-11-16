# -*- coding: utf-8 -*-
"""data/src/part{N}/*.json（生成バッチごとの問題ファイル）を読み込み、
data/items.json・data/sets.json・data/bank.js を書き出す。
  python3 scripts/build_data.py
行の形は supabase/schema.sql の items / sets テーブルと一致させている。
問題ファイルの書き方は data/src/README.md を参照。"""
import json, pathlib, datetime, re, sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "data" / "src"

# 問題ファイルに書ける項目（それ以外はタイプミスとみなしてエラー）
FILE_KEYS = {"batch", "source", "note", "sets", "items"}
SET_REQ = {"id", "kind", "scene", "translation_ja", "questions"}
SET_OPT = {"part", "speakers", "segments", "passages", "graphic", "image", "status", "source"}
ITEM_REQ = {"id", "type", "scene", "level", "prompt", "options", "answer", "explanation_ja", "translation_ja"}
ITEM_OPT = {"part", "shuffle", "translation_options_ja", "status", "source", "voices"}
STATUS_IN_SRC = {"draft", "retired"}  # reviewed / flagged はレビュー結果から自動で決まる

errors, items, sets, batches = [], [], [], []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def check_keys(where, d, req, opt):
    if not isinstance(d, dict):
        err(where, "オブジェクト（{...}）ではない"); return False
    for k in sorted(req - d.keys()): err(where, f"{k} がない")
    for k in sorted(d.keys() - req - opt): err(where, f"知らない項目 {k}（書き間違い？）")
    return not (req - d.keys())


def default_voices(iid, part):
    """Part 1・2 の話者の性別。ID の番号の偶奇で男女を交互にする（問題を足しても既存の声は変わらない）"""
    odd = int(iid.split("-")[1]) % 2 == 1
    if part == 1: return {"options": "female" if odd else "male"}
    return {"stem": "male", "options": "female"} if odd else {"stem": "female", "options": "male"}


def make_item(where, d, part, source, set_id):
    if not check_keys(where, d, ITEM_REQ, ITEM_OPT): return
    iid = d["id"]
    if not re.fullmatch(rf"p{part}-\d{{4}}", str(iid)): err(where, f"ID {iid} が p{part}-0000 の形でない")
    if d.get("part", part) != part: err(where, f"part {d['part']} がフォルダ part{part} と違う")
    status = d.get("status", "draft")
    if status not in STATUS_IN_SRC: err(where, f"status は draft か retired（{status}）")
    opts = []
    for n, o in enumerate(d["options"]):
        if isinstance(o, str): opts.append({"id": "abcd"[n], "text": o})
        elif isinstance(o, dict) and set(o) == {"id", "text"}: opts.append(o)
        else: err(where, f"選択肢 {n + 1} の形が違う（文字列か {{\"id\", \"text\"}}）")
    row = dict(id=iid, part=part, set_id=set_id, type=d["type"], scene=d["scene"], prompt=d["prompt"],
               options=opts, answer=d["answer"], shuffle=d.get("shuffle", True),
               explanation_ja=d["explanation_ja"], translation_ja=d["translation_ja"],
               translation_options_ja=d.get("translation_options_ja"), level=d["level"],
               status=status, source=d.get("source", source), review=[])
    if part in (1, 2): row["voices"] = d.get("voices") or default_voices(iid, part)
    items.append(row)
    return iid


def make_set(where, d, part, source):
    if not check_keys(where, d, SET_REQ, SET_OPT): return
    sid = d["id"]
    # セットIDは p{N}-s000（Part 1 の試作3件だけは p1-s0001 の4桁。既存IDは変えない）
    if not re.fullmatch(rf"p{part}-s\d{{3,4}}", str(sid)): err(where, f"ID {sid} が p{part}-s000 の形でない")
    if d.get("part", part) != part: err(where, f"part {d['part']} がフォルダ part{part} と違う")
    status = d.get("status", "draft")
    if status not in STATUS_IN_SRC: err(where, f"status は draft か retired（{status}）")
    if not d["questions"]: err(where, "questions が空")
    src = d.get("source", source)
    qids = [make_item(f"{where} > {q.get('id', f'設問{n + 1}') if isinstance(q, dict) else f'設問{n + 1}'}", q, part, src, sid)
            for n, q in enumerate(d["questions"])]
    sets.append(dict(id=sid, part=part, kind=d["kind"], scene=d["scene"], speakers=d.get("speakers") or [],
                     segments=d.get("segments") or [], passages=d.get("passages") or [],
                     graphic=d.get("graphic"), image=d.get("image"), question_ids=[q for q in qids if q],
                     translation_ja=d["translation_ja"], status=status, source=src))


# ------------------------------------------------------------ 問題ファイルを読む
files = sorted(SRC_DIR.glob("part*/*.json"))
if not files: sys.exit(f"{SRC_DIR.relative_to(ROOT)}/part*/*.json が見つかりません")
for f in files:
    rel = f.relative_to(ROOT)
    m = re.fullmatch(r"part([1-7])", f.parent.name)
    if not m: err(rel, "フォルダ名は part1〜part7"); continue
    part = int(m.group(1))
    try:
        doc = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(rel, f"JSON の形が正しくない（{e.lineno}行目 {e.colno}文字目: {e.msg}）"); continue
    if not check_keys(rel, doc, {"batch", "source"}, FILE_KEYS - {"batch", "source"}): continue
    batches.append(doc["batch"])
    for n, s in enumerate(doc.get("sets", [])):
        make_set(f"{rel} > {s.get('id', f'セット{n + 1}') if isinstance(s, dict) else f'セット{n + 1}'}", s, part, doc["source"])
    for n, it in enumerate(doc.get("items", [])):
        where = f"{rel} > {it.get('id', f'問題{n + 1}') if isinstance(it, dict) else f'問題{n + 1}'}"
        if part in (1, 3, 4, 6, 7): err(where, f"Part{part} の設問は sets の questions に入れる"); continue
        make_item(where, it, part, doc["source"], None)

for k, n in Counter(i["id"] for i in items).items():
    if n > 1: err(k, f"同じIDが {n} 回出てくる")
for k, n in Counter(s["id"] for s in sets).items():
    if n > 1: err(k, f"同じセットIDが {n} 回出てくる")
if errors:
    for e in errors: print("エラー:", e)
    sys.exit(f"問題ファイルにエラーが {len(errors)} 件あります。直してからもう一度実行してください（出力は更新していません）。")

items.sort(key=lambda i: (i["part"], i["id"]))
sets.sort(key=lambda s: (s["part"], s["id"]))

# ------------------------------------------------------------ レビュー結果を反映（scripts/import_review.py が作る）
rpath = ROOT / "data" / "reviews.json"
if rpath.exists():
    reviews = json.loads(rpath.read_text(encoding="utf-8"))
    for it in items:
        rs = reviews.get(it["id"])
        if not rs: continue
        it["review"] = rs
        if it["status"] == "retired": continue
        bad = any((not r["agree"]) or r.get("ambiguous") or r.get("issues") for r in rs)
        it["status"] = "flagged" if bad else "reviewed"

# ------------------------------------------------------------ 書き出し
(ROOT / "data" / "items.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "data" / "sets.json").write_text(json.dumps(sets, ensure_ascii=False, indent=1), encoding="utf-8")
ub = list(dict.fromkeys(batches))
VERSION = datetime.date.today().isoformat() + "-" + (ub[0] if len(ub) == 1 else f"{len(ub)}batches")
(ROOT / "data" / "bank.js").write_text(
    "// 自動生成（scripts/build_data.py）。file:// でも読めるように JSON を JS として置いている\n"
    "window.BANK = " + json.dumps({"version": VERSION, "items": items, "sets": sets}, ensure_ascii=False) + ";\n", encoding="utf-8")
live = [i for i in items if i["status"] != "retired"]
print(len(files), "files |", len(live), "items", dict(sorted(Counter(i["part"] for i in live).items())), "|", len(sets), "sets",
      f"| retired {len(items) - len(live)}" if len(items) != len(live) else "")
