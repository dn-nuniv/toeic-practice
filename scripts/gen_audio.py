#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Cloud Text-to-Speech で Listening（Part 1〜4）の音声をまとめて作る。
追加のライブラリは不要（Python 3.8 以上の標準機能だけで動く）。

使い方（Mac のターミナルで、このリポジトリのフォルダに移動してから）:
  python3 scripts/gen_audio.py --dry-run        # 文字数と作るファイル数を確認するだけ（APIは呼ばない）
  python3 scripts/gen_audio.py                  # 米国・英国・オーストラリアの音声を作る
  python3 scripts/gen_audio.py --regions us     # 米国だけ

API キーは環境変数 GOOGLE_TTS_API_KEY（なければ GOOGLE_API_KEY）から読む（画面やファイルには書き出さない）。
Cloud Text-to-Speech 用のキー（AIza で始まる）が必要。Gemini API のキーでは 401 になる。
同じ文・同じ声の音声はすでにあれば作り直さないので、問題を追加したら同じコマンドを実行するだけでよい。
音声のキーは js/audio.js と同じ規則:
  Part 1・2 の選択肢 <item>:opt:<option> / Part 2 の質問 <item>:stem / Part 3・4 <set>:seg:<n> / Part 3・4 の設問 <item>:q / 記号 label:A:female
Part 3・4 の設問はナレーター（男性の声のうち、会話で使わない最後の声）が読む。
単語 <単語ID>:word と例文 <単語ID>:ex（data/vocab.json）も作る。
"""
import argparse, base64, hashlib, json, os, pathlib, sys, time, urllib.request, urllib.error, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://texttospeech.googleapis.com/v1"
LANG = {"us": "en-US", "gb": "en-GB", "au": "en-AU"}  # カナダは外した（Google の TTS にカナダ英語の声がない。米国英語に近い）
TIERS = ["Neural2", "Wavenet", "Standard"]  # 上から順に使える声を探す
NARRATOR = "male"  # Part 3・4 の設問を読む声の性別（js/audio.js の NARRATOR と同じにする）


KEY_IN_URL = False  # まずヘッダーで送り、断られたら URL の ?key= で送り直す


def call(method, path, key, body=None, retries=4):
    global KEY_IN_URL
    data = json.dumps(body).encode() if body is not None else None
    for i in range(retries):
        url, headers = f"{API}/{path}", {"Content-Type": "application/json"}
        if KEY_IN_URL: url += f"{'&' if '?' in path else '?'}key={urllib.parse.quote(key)}"
        else: headers["X-Goog-Api-Key"] = key
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (401, 403) and not KEY_IN_URL:
                KEY_IN_URL = True; continue
            if e.code in (429, 500, 503) and i < retries - 1:
                time.sleep(2 ** i); continue
            hint = ("\n→ キーが Text-to-Speech で使えない種類か、権限が足りません。Google Cloud コンソールの「認証情報」で作った"
                    " API キー（AIza で始まる）か、そのプロジェクトで Cloud Text-to-Speech API が有効か、"
                    "キーの「API の制限」に Text-to-Speech が含まれているかを確認してください。") if e.code in (401, 403) else ""
            sys.exit(f"API エラー {e.code}: {msg}{hint}")
        except urllib.error.URLError as e:
            if i < retries - 1: time.sleep(2 ** i); continue
            sys.exit(f"接続エラー: {e}")


def pick_voices(key, region, tier_pref):
    """地域ごとに、男女それぞれ使う声の一覧を決める"""
    lang = LANG[region]
    vs = call("GET", f"voices?languageCode={lang}", key).get("voices", [])
    vs = [v for v in vs if lang in v.get("languageCodes", [])]
    out = {}
    for g in ("FEMALE", "MALE"):
        cand = [v["name"] for v in vs if v.get("ssmlGender") == g]
        for t in ([tier_pref] if tier_pref else []) + TIERS:
            hit = sorted(n for n in cand if f"-{t}-" in n)
            if hit: out[g.lower()] = hit; break
    return out


def utterances(bank):
    """作る音声の一覧 (key, text, gender, speaker_index)"""
    items, sets = bank["items"], {s["id"]: s for s in bank["sets"]}
    u, labels = [], set()
    for it in items:
        if it["part"] not in (1, 2): continue
        g = it.get("voices", {})
        if it["part"] == 2: u.append((f"{it['id']}:stem", it["prompt"], g.get("stem", "female"), 0))
        og = g.get("options", "male")
        for o in it["options"]: u.append((f"{it['id']}:opt:{o['id']}", o["text"], og, 0))
        labels.add(og)
    for s in sets.values():
        if s["part"] not in (3, 4): continue
        spk = {p["id"]: p for p in s["speakers"]}
        # 同じ性別の話者が複数いるときは別の声にする
        nth, cnt = {}, {}
        for p in s["speakers"]:
            cnt[p["gender"]] = cnt.get(p["gender"], 0); nth[p["id"]] = cnt[p["gender"]]; cnt[p["gender"]] += 1
        for i, sg in enumerate(s["segments"]):
            p = spk[sg["speaker"]]
            u.append((f"{s['id']}:seg:{i}", sg["text"], p["gender"], nth[p["id"]]))
    # Part 3・4 の設問の読み上げ（ナレーター。nth=-1 で男性の声の一覧の最後を使い、会話の話し手と分ける）
    for it in items:
        if it["part"] in (3, 4): u.append((f"{it['id']}:q", it["prompt"], NARRATOR, -1))
    for g in sorted(labels):
        for L in "ABCD": u.append((f"label:{L}:{g}", L + ".", g, 0))
    return u


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regions", default="us,gb,au", help="作る地域（us,gb,au）")
    ap.add_argument("--tier", default="", help="声の種類を指定（例 Neural2, Wavenet, Standard）")
    ap.add_argument("--rate", type=float, default=1.0, help="話す速さ（1.0 が標準）")
    ap.add_argument("--dry-run", action="store_true", help="APIを呼ばずに、作る数と文字数だけ表示する")
    a = ap.parse_args()

    text = (ROOT / "data/bank.js").read_text(encoding="utf-8")
    bank = json.loads(text[text.index("=") + 1:].rstrip().rstrip(";"))
    us = utterances(bank)
    # 単語と例文（js/vocab.js の発音ボタン）。キーは <単語ID>:word と <単語ID>:ex
    vpath = ROOT / "data/vocab.json"
    if vpath.exists():
        for w in json.loads(vpath.read_text(encoding="utf-8")):
            if w.get("status") == "retired": continue
            us.append((f"{w['id']}:word", w["word"], "female", 0))
            us.append((f"{w['id']}:ex", w["example"], "female", 0))
    mpath = ROOT / "audio/manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    regions = [r.strip() for r in a.regions.split(",") if r.strip()]

    key = os.environ.get("GOOGLE_TTS_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    if not a.dry_run and not key:
        sys.exit("環境変数 GOOGLE_TTS_API_KEY が設定されていません。")

    total_chars = total_new = 0
    for region in regions:
        if region not in LANG: print(f"未対応の地域: {region}"); continue
        if a.dry_run:
            m = manifest.get(region, {})
            # キーがない、または文が変わった（記録した声で計算したハッシュが違う）ものを数える
            new = [x for x in us if x[0] not in m or
                   m[x[0]].get("hash") != hashlib.sha1(f"{x[1]}|{m[x[0]].get('voice')}|{a.rate}".encode()).hexdigest()[:12]]
            c = sum(len(x[1]) for x in new); total_chars += c; total_new += len(new)
            print(f"[{region}] 音声 {len(us)} 件（新しく作る {len(new)} 件・{c:,} 文字）")
            continue
        voices = pick_voices(key, region, a.tier)
        if not voices.get("female") or not voices.get("male"):
            print(f"[{region}] {LANG[region]} の男女の声がそろわないため飛ばします（見つかった声: {voices}）"); continue
        print(f"[{region}] 女性 {voices['female'][:2]} / 男性 {voices['male'][:2]}")
        outdir = ROOT / "audio" / region; outdir.mkdir(parents=True, exist_ok=True)
        m = manifest.setdefault(region, {})
        made = 0
        for k, t, g, nth in us:
            vname = voices[g][nth % len(voices[g])]
            h = hashlib.sha1(f"{t}|{vname}|{a.rate}".encode()).hexdigest()[:12]
            fname = f"audio/{region}/{k.replace(':', '_')}.mp3"
            if m.get(k, {}).get("hash") == h and (ROOT / fname).exists(): continue
            body = {"input": {"text": t}, "voice": {"languageCode": LANG[region], "name": vname},
                    "audioConfig": {"audioEncoding": "MP3", "speakingRate": a.rate}}
            r = call("POST", "text:synthesize", key, body)
            (ROOT / fname).write_bytes(base64.b64decode(r["audioContent"]))
            m[k] = {"file": fname, "hash": h, "voice": vname}
            made += 1; total_chars += len(t)
            if made % 20 == 0:
                print(f"  {made} 件作成…"); mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
            time.sleep(0.05)
        total_new += made
        print(f"[{region}] 新しく {made} 件作成")

    if a.dry_run:
        print(f"合計：新しく作る音声 {total_new} 件・{total_chars:,} 文字（無料枠の目安：Neural2 は毎月100万文字）")
        return
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "audio/manifest.js").write_text("// 自動生成（scripts/gen_audio.py）\nwindow.AUDIO_MANIFEST = " + json.dumps(manifest, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"完了：新しく {total_new} 件・{total_chars:,} 文字。audio/manifest.js を更新しました。")


if __name__ == "__main__":
    main()
