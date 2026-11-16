# -*- coding: utf-8 -*-
"""レビュー役（Orca など）が返した JSON を取り込み、正解と照合する。
  python3 scripts/import_review.py review/orca_result.json --reviewer orca
結果は data/reviews.json に追記され、次に build_data.py を実行すると各問題の状態に反映される。
  一致して曖昧さの指摘もない → reviewed（レビュー済み）
  正解が食い違う／曖昧・誤りの指摘がある → flagged（要確認）
各レビューにはそのときの問題の版（content_hash）を記録する。問題を直すと古いレビューは効かなくなり、
その問題は draft に戻って、次の export_review.py の対象になる。

指摘を検討した結果、問題を直さないと決めたときは理由を記録する（その問題の今の版への指摘がすべて解決済みになる）:
  python3 scripts/import_review.py --resolve p7-0008 --note "most likely の推論で一意に決まる。変更不要"
"""
import json, pathlib, argparse, datetime, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from review_hash import content_hash
import vocab_lib as V

ap = argparse.ArgumentParser()
ap.add_argument("file", nargs="?", help="レビュー役が返した JSON のファイル")
ap.add_argument("--reviewer", help="レビュー役の名前（orca, gpt など）")
ap.add_argument("--resolve", metavar="ID", help="この問題への指摘を解決済みにする")
ap.add_argument("--note", help="--resolve の理由")
a = ap.parse_args()

items = {i["id"]: i for i in json.loads((ROOT / "data/items.json").read_text(encoding="utf-8"))}
sets = {s["id"]: s for s in json.loads((ROOT / "data/sets.json").read_text(encoding="utf-8"))}
# 単語（v-）も同じ形で取り込む。英→日の4択の並びは data/vocab.json の choices の順
vocab = {w["id"]: w for w in json.loads((ROOT / "data/vocab.json").read_text(encoding="utf-8"))} if (ROOT / "data/vocab.json").exists() else {}
meaning = {k: w["meaning_ja"] for k, w in vocab.items()}
rpath = ROOT / "data/reviews.json"
reviews = json.loads(rpath.read_text(encoding="utf-8")) if rpath.exists() else {}
now = datetime.datetime.now().isoformat(timespec="seconds")


def chash(it):
    if it["id"].startswith("v-"): return V.content_hash(it, meaning)
    return content_hash(it, sets.get(it.get("set_id")))


def key_letter(it):
    if it["id"].startswith("v-"): return "ABCD"[it["choices"].index(it["id"])]
    return "ABCD"[[o["id"] for o in it["options"]].index(it["answer"])]


def is_bad(r):
    return (not r["agree"]) or r.get("ambiguous") or r.get("issues")


if a.resolve:
    if not a.note: sys.exit("--note で理由を書いてください")
    it = items.get(a.resolve) or vocab.get(a.resolve)
    if not it: sys.exit(f"不明なID: {a.resolve}")
    h = chash(it)
    targets = [r for r in reviews.get(it["id"], []) if r.get("content_hash", h) == h and is_bad(r) and not r.get("resolved")]
    if not targets: sys.exit(f"{it['id']}: 今の版の問題に未解決の指摘はありません")
    for r in targets: r["resolved"] = {"at": now, "note": a.note}
    rpath.write_text(json.dumps(reviews, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{it['id']}: 指摘 {len(targets)} 件を解決済みにしました。python3 scripts/build_data.py で状態に反映されます。")
    sys.exit()

if not (a.file and a.reviewer): ap.error("レビュー結果のファイルと --reviewer を指定してください")
raw = pathlib.Path(a.file).read_text(encoding="utf-8")
m = re.search(r"\[.*\]", raw, re.S)  # 前後に説明文が付いていても JSON 部分だけ読む
res = json.loads(m.group(0) if m else raw)
agree = disagree = flagged = 0
for r in res:
    it = items.get(r.get("id")) or vocab.get(r.get("id"))
    if not it: print("不明なID:", r.get("id")); continue
    letter = str(r.get("answer", "")).strip().strip("()").upper()[:1]
    key = key_letter(it)
    ok = letter == key
    issues = (r.get("issues") or "").strip()
    reviews.setdefault(it["id"], []).append({"reviewer": a.reviewer, "at": now, "answer": letter, "key": key, "agree": ok,
                                             "ambiguous": bool(r.get("ambiguous")), "confidence": r.get("confidence"), "issues": issues,
                                             "content_hash": chash(it)})
    if ok: agree += 1
    else: disagree += 1; print(f"不一致 {it['id']}: レビュー {letter} / 正解 {key}  {issues}")
    if r.get("ambiguous") or issues: flagged += 1; print(f"指摘 {it['id']}: {'曖昧 ' if r.get('ambiguous') else ''}{issues}")
rpath.write_text(json.dumps(reviews, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"一致 {agree} / 不一致 {disagree} / 指摘あり {flagged}。python3 scripts/build_data.py を実行すると状態に反映されます。")
