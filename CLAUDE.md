# CLAUDE.md — TOEIC L&R 練習アプリ

このリポジトリで作業するときの前提と手順。作業を始める前に必ず読むこと。

## 目的と段階
- AI で作った TOEIC L&R 形式の**オリジナル問題**を、シャッフル・復習スケジュール・音声つきで練習する授業補助アプリ。
- **段階1（今）**：サーバーなしの静的サイト。学習記録はブラウザ（localStorage）。リポジトリは private のまま進める（GitHub Pages は後で）。
- **段階2（予定）**：Next.js＋Supabase のログイン付きアプリ（先生の既存の JLPT アプリと同じ構成）。段階1のデータ形式と `js/store.js` の関数の形は、そのまま移せるように保つこと。
- 正確さの基準：市販教材ほどの厳密さは求めない。機械チェック＋別AI（Orca）との相互レビューで十分。

## 構成
- `index.html`, `css/`, `js/`：アプリ本体。`js/store.js` は保存先の差し替え口（段階2で Supabase 版にする）。
- `data/src/part{N}/*.json`：**問題の元データ**（生成バッチごとに1ファイル）。書き方は `data/src/README.md`。
- `data/items.json`, `data/sets.json`：問題データ（1件＝Supabase の1行）。`data/bank.js` はアプリが読むまとめ版。この3つは `build_data.py` が `data/src` から作る（手で編集しない）。
- `data/blueprint.json`：大量生成の設計表（Part × 出題タイプ × 場面）。
- `data/reviews.json`：相互レビューの結果（`import_review.py` が作る）。
- `scripts/`：`build_data.py`（データ作成）、`validate.py`（機械チェック）、`export_review.py` / `import_review.py`（相互レビュー）、`gen_audio.py`（音声）。
- `supabase/schema.sql`：段階2のテーブル案。`images/part1/`：Part 1 の写真。`audio/`：生成した音声と manifest。

## 作業の流れ（問題を増やすとき）
1. `data/blueprint.json` の升目を指定して問題を作り、`data/src/part{N}/<バッチ名>.json` として新しいファイルで置く（既存ファイルの問題は書き換えない。形は `data/src/README.md`）
2. `python3 scripts/build_data.py` — 書き方の誤り（知らない項目・必須項目の欠け・ID の形・重複）があるとエラーで止まる
3. `python3 scripts/validate.py` — **エラー0件になるまで直す**。警告も目を通す
4. `python3 scripts/export_review.py` → `review/PROMPT.md` と `review/packet.md` を先生が Orca に渡す → 返ってきた JSON を `python3 scripts/import_review.py <file> --reviewer orca` → もう一度 `build_data.py`
5. `python3 scripts/gen_audio.py --dry-run` で件数と文字数を確認 → `python3 scripts/gen_audio.py`
6. ブラウザで `index.html` を開いて確認 → コミット・push（コミットメッセージは日本語）

## 問題を作るときのルール
- **オリジナルのみ**。TOEIC 公式問題・市販教材・他のAI教材の英文や設定を流用しない。人名・会社名は架空、メールアドレスや URL は `.example` ドメイン。
- 正解は**ただ1つに決まる**こと。言い換え（paraphrase）で正解を作り、誤答は「本文の語をそのまま使ったひっかけ」「部分的に合っている」「本文にない」などで作る。正解の選択肢だけが長い・詳しい、を避ける。
- 正解は表示位置ではなく**選択肢ID**（a/b/c/d）で持つ。金額・日付の昇順や [1]〜[4] の位置など、並びに意味がある問題は `shuffle: false`。
- Part 1：選択肢は写真と照合して1つだけ正しいこと。人のいない写真で being（進行中の動作）は誤答。写真を作ったら必ず目で確認する。
- Part 2：選択肢3つ。同じ語・似た音のひっかけを入れる。間接的な応答が正解の問題も一定数入れる。
- Part 3・4：1セット3問。図表問題・発言の意図を問う問題・3人の会話も含める。
- Part 6：1セット4問、うち1問は文挿入。空欄は本文中に `[1]`〜`[4]`。
- Part 7：単一文書・チャット・ダブル／トリプルパッセージ。照合問題（cross.reference）を入れる。位置を問う問題の本文は `— [1] —` の形。
- 解説（`explanation_ja`）は根拠の英文を短く引用し、なぜ他が違うかを1文で。和訳（`translation_ja`、`translation_options_ja`）をつける。
- ID は `p{Part}-{4桁}`、セットは `p{Part}-s{3桁}`（試作の Part 1 の3セットだけ `p1-s0001` の4桁）。既存の ID は変えない（学習記録が ID に紐づくため）。不要になった問題は削除せず `status: "retired"`。
- `status` は draft → reviewed / flagged（import_review が自動で設定）。

## 音声（Google Cloud Text-to-Speech）
- `scripts/gen_audio.py` は環境変数 `GOOGLE_TTS_API_KEY`（なければ `GOOGLE_API_KEY`）を使う。Cloud Text-to-Speech 用の `AIza` で始まるキーが必要（Gemini API のキーは使えない）。**キーを表示・ログ出力・ファイル保存・コミットしない**。
- 同じ文・同じ声は作り直さない（manifest の hash で判定）。Neural2 → WaveNet → Standard の順に声を選ぶ。
- 音声のキーは `js/audio.js` と共通の規則（`<item>:opt:<id>`, `<item>:stem`, `<set>:seg:<n>`, `label:A:female`）。変えるときは両方を直す。
- Part 1・2 の話者の性別は `build_data.py` が `voices` に設定する。

## Part 1 の写真
- 試作の3枚は Gamma の画像生成（1枚70クレジット、残り150）。数を増やすときは Google Cloud の Imagen など別手段を検討し、費用がかかる生成は先生に確認してから行う。
- 1600px 幅の WebP にして `images/part1/<item id>.webp` に置く。

## 次にやること（TODO）
1. ~~問題データの置き場所を変える~~ → 済み（`data/src/part{N}/*.json` を読む形。試作49問は `pilot-v0.json` に移した。出力は移行前と同一）
2. `data/blueprint.json` に沿って Part ごとに生成（例：Part 5 を30問ずつ）。生成のたびに validate とレビュー用の書き出し。
3. 語彙レベルの判定：NGSL / TSL（CC BY-SA 4.0、出典表示が必要）を取り込み、各問題の語彙をプロファイルする。
4. Part 3・4 の設問の読み上げ（本番では設問も音声で流れる）。
5. 段階2：JLPT アプリの構成に合わせて Supabase へ移行（`supabase/schema.sql`）。

## 確認のしかた
- `python3 scripts/validate.py` がエラー0件であること。
- ブラウザで index.html を開き、各 Part を1問ずつ解いて、表示・採点・解説・音声を確認する。
- 学習記録の形（`user_progress` / `attempts`）を変えるときは `supabase/schema.sql` も合わせて直す。
