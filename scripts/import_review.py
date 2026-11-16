# -*- coding: utf-8 -*-
"""レビュー役（Orca など）が返した JSON を取り込み、正解と照合する。
  python3 scripts/import_review.py review/orca_result.json --reviewer orca
結果は data/reviews.json に追記され、次に build_data.py を実行すると各問題の状態に反映される。
  一致して曖昧さの指摘もない → reviewed（レビュー済み）
  正解が食い違う／曖昧・誤りの指摘がある → flagged（要確認）"""
import json, pathlib, argparse, datetime, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--reviewer", required=True); a = ap.parse_args()
raw = pathlib.Path(a.file).read_text(encoding="utf-8")
m = re.search(r"\[.*\]", raw, re.S)  # 前後に説明文が付いていても JSON 部分だけ読む
res = json.loads(m.group(0) if m else raw)
items = {i["id"]: i for i in json.loads((ROOT / "data/items.json").read_text(encoding="utf-8"))}
rpath = ROOT / "data/reviews.json"
reviews = json.loads(rpath.read_text(encoding="utf-8")) if rpath.exists() else {}
now = datetime.datetime.now().isoformat(timespec="seconds")
agree = disagree = flagged = 0
for r in res:
    it = items.get(r.get("id"))
    if not it: print("不明なID:", r.get("id")); continue
    letter = str(r.get("answer", "")).strip().strip("()").upper()[:1]
    key_letter = "ABCD"[[o["id"] for o in it["options"]].index(it["answer"])]
    ok = letter == key_letter
    issues = (r.get("issues") or "").strip()
    reviews.setdefault(it["id"], []).append({"reviewer": a.reviewer, "at": now, "answer": letter, "key": key_letter, "agree": ok,
                                             "ambiguous": bool(r.get("ambiguous")), "confidence": r.get("confidence"), "issues": issues})
    if ok: agree += 1
    else: disagree += 1; print(f"不一致 {it['id']}: レビュー {letter} / 正解 {key_letter}  {issues}")
    if r.get("ambiguous") or issues: flagged += 1; print(f"指摘 {it['id']}: {'曖昧 ' if r.get('ambiguous') else ''}{issues}")
rpath.write_text(json.dumps(reviews, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"一致 {agree} / 不一致 {disagree} / 指摘あり {flagged}。python3 scripts/build_data.py を実行すると状態に反映されます。")
