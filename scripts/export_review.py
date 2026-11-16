# -*- coding: utf-8 -*-
"""別のAI（Orca など）に解かせて照合するためのレビュー用ファイルを書き出す。
  python3 scripts/export_review.py            # まだレビューしていない問題だけ
  python3 scripts/export_review.py --all      # すべての問題
出力：review/packet.md（正解を伏せた問題集）と review/PROMPT.md（レビュー役への指示文）。
レビュー役には PROMPT.md と packet.md を渡し、返ってきた JSON を
  python3 scripts/import_review.py <返ってきたファイル> --reviewer orca
で取り込む。"""
import json, pathlib, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser(); ap.add_argument("--all", action="store_true"); a = ap.parse_args()
items = json.loads((ROOT / "data/items.json").read_text(encoding="utf-8"))
sets = {s["id"]: s for s in json.loads((ROOT / "data/sets.json").read_text(encoding="utf-8"))}
target = [i for i in items if a.all or i["status"] == "draft"]
L = "ABCD"
out, done_sets = ["# TOEIC 練習問題 レビュー用（正解は伏せてある）\n"], set()
for it in target:
    s = sets.get(it.get("set_id"))
    if s and s["id"] not in done_sets:
        done_sets.add(s["id"])
        out.append(f"\n---\n## セット {s['id']}（Part {s['part']}）\n")
        if s.get("image"): out.append(f"[写真] {s['image']}（写真はファイルを参照。描写の正しさは写真と照らし合わせて確認）\n")
        if s["segments"]: out.append("**スクリプト（音声で流れる）**\n\n" + "\n".join(f"- {g['speaker']}: {g['text']}" for g in s["segments"]) + "\n")
        if s.get("graphic"):
            gr = s["graphic"]; out.append(f"**図：{gr['title']}**\n\n| " + " | ".join(gr["columns"]) + " |\n|" + "---|" * len(gr["columns"]) + "\n" + "\n".join("| " + " | ".join(r) + " |" for r in gr["rows"]) + "\n")
        for p in s["passages"]:
            if p.get("header"): out.append("\n".join(f"{k}: {v}" for k, v in p["header"].items()))
            if p.get("title"): out.append(f"**{p['title']}**")
            if p.get("table"):
                t = p["table"]; out.append("| " + " | ".join(t["columns"]) + " |\n|" + "---|" * len(t["columns"]) + "\n" + "\n".join("| " + " | ".join(r) + " |" for r in t["rows"]))
            out.append(p.get("text", "") + "\n")
    out.append(f"\n### {it['id']}（Part {it['part']}）\n{it['prompt']}\n")
    out.append("\n".join(f"({L[k]}) {o['text']}" for k, o in enumerate(it["options"])) + "\n")
(ROOT / "review").mkdir(exist_ok=True)
(ROOT / "review/packet.md").write_text("\n".join(out), encoding="utf-8")
(ROOT / "review/PROMPT.md").write_text("""あなたは英語検定問題の校閲者です。添付の packet.md にある TOEIC L&R 形式の練習問題を、正解を見ずに自分で解いてください。
各問題について次を確認してください。
1. 正解がただ1つに決まるか（2つ以上が正解になりうる、または正解がない場合は ambiguous を true）
2. 英文として自然か、文法の誤りがないか
3. 本文・スクリプト・図と設問の内容が矛盾していないか
4. Part 1 は写真を見られない場合、写真の確認はせず other の項目だけ確認する

出力は JSON 配列だけにしてください（説明文は不要）。形式：
[{"id": "p5-0001", "answer": "C", "ambiguous": false, "confidence": 0.9, "issues": "問題がなければ空文字"}]
answer は (A)〜(D) の記号の英字1文字。
""", encoding="utf-8")
print(f"{len(target)} 問を review/packet.md に書き出しました。review/PROMPT.md と一緒にレビュー役に渡してください。")
