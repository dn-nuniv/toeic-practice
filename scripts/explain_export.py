# -*- coding: utf-8 -*-
"""解説の確認用の書き出し（export_review.py --explain から呼ばれる）。
正解のレビュー（正解を伏せて解いてもらう）とは逆に、正解と解説をすべて見せて、解説・和訳の誤りを探してもらう。"""
L = "ABCD"


def table(t):
    return "| " + " | ".join(t["columns"]) + " |\n|" + "---|" * len(t["columns"]) + "\n" + "\n".join("| " + " | ".join(r) + " |" for r in t["rows"])


def run(ROOT, items, sets, a):
    target = [i for i in items if i["status"] != "retired" and (a.all or i.get("explain_status") == "unchecked")]
    if a.part: target = [i for i in target if i["part"] == a.part]
    if a.limit:  # セットの途中では切らない
        cut, n = [], 0
        for it in target:
            if n >= a.limit and not (cut and it.get("set_id") and it.get("set_id") == cut[-1].get("set_id")): break
            cut.append(it); n += 1
        target = cut
    out, done_sets = ["# TOEIC 練習問題 解説の確認用（正解・解説・和訳つき）\n"], set()
    for it in target:
        s = sets.get(it.get("set_id"))
        if s and s["id"] not in done_sets:
            done_sets.add(s["id"])
            out.append(f"\n---\n## セット {s['id']}（Part {s['part']}）\n")
            if s.get("image"): out.append(f"[写真] {s['image']}（写真を見られない場合、写真との一致は確認しなくてよい）\n")
            if s["segments"]: out.append("**スクリプト（音声）**\n\n" + "\n".join(f"- {g['speaker']}: {g['text']}" for g in s["segments"]) + "\n")
            if s.get("graphic"): out.append(f"**図：{s['graphic']['title']}**\n\n" + table(s["graphic"]) + "\n")
            for p in s["passages"]:
                if p.get("header"): out.append("\n".join(f"{k}: {v}" for k, v in p["header"].items()))
                if p.get("title"): out.append(f"**{p['title']}**")
                if p.get("table"): out.append(table(p["table"]))
                out.append(p.get("text", "") + "\n")
            if s.get("translation_ja"): out.append("**本文・スクリプトの訳**\n\n" + s["translation_ja"] + "\n")
        tro = it.get("translation_options_ja") or [""] * len(it["options"])
        notes = it.get("option_notes_ja") or [""] * len(it["options"])
        ans = L[[o["id"] for o in it["options"]].index(it["answer"])]
        out.append(f"\n### {it['id']}（Part {it['part']}）\n{it['prompt']}\n")
        if it.get("translation_ja"): out.append(f"設問の訳：{it['translation_ja']}\n")
        out.append("\n".join(f"({L[k]}) {o['text']}" + (f"　〔訳〕{tro[k]}" if tro[k] else "") + (f"\n    コメント：{notes[k]}" if notes[k] else "")
                             for k, o in enumerate(it["options"])))
        out.append(f"\n**正解：({ans})**\n正解の理由：{it['explanation_ja']}")
        if it.get("point_ja"): out.append(f"TOEIC のポイント：{it['point_ja']}")
        out.append("")
    (ROOT / "review").mkdir(exist_ok=True)
    (ROOT / "review/explain_packet.md").write_text("\n".join(out), encoding="utf-8")
    (ROOT / "review/EXPLAIN_PROMPT.md").write_text("""あなたは英語教材の校閲者です。添付の explain_packet.md には、TOEIC L&R 形式の練習問題と、その正解・解説・和訳が載っています。
正解はすでに別のレビューで確かめてあります。今回は、日本人の学習者が読む**解説と和訳に誤りがないか**を確認してください。

各問題について、次を確認してください。
1. 正解の理由：引用している英文が本文・スクリプトに実際にあるか。理由の説明が正しいか
2. 選択肢ごとのコメント：各選択肢がなぜ正解・不正解なのかの説明が正しいか（本文にないことを「書かれている」と言っていないか、文法の説明に誤りがないか）
3. 和訳：設問・選択肢・本文の訳に誤訳や抜けがないか
4. TOEIC のポイント：一般的な説明として正しいか（言い過ぎ・例外の無視がないか）
5. 日本語として自然で、学習者に分かりやすいか（細かい言い回しの好みは指摘しなくてよい）
（解説の中の (A)〜(D) は、この資料の選択肢の並びの記号です）

出力は JSON 配列だけにしてください（説明文は不要）。形式：
[{"id": "p5-0001", "ok": true, "issues": "", "fix": ""}]
- ok：誤りがなければ true、直すべき誤りがあれば false
- issues：誤りの内容（どの部分の何が違うか）。なければ空文字
- fix：直し方の案（任意）
""", encoding="utf-8")
    print(f"{len(target)} 問を review/explain_packet.md に書き出しました（{len(done_sets)} セットを含む）。review/EXPLAIN_PROMPT.md と一緒にレビュー役に渡してください。")
    print("返ってきた JSON は  python3 scripts/import_review.py <ファイル> --reviewer orca --explain  で取り込みます。")
